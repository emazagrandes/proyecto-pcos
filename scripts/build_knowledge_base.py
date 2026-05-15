import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR, REPORTS_DIR
from llm_support import EXTRACTION_SCHEMA_VERSION


SOURCE_PRIORITY = {"pubmed": 3, "openalex": 2}
NOISE_TRIAL_INTERVENTIONS = {
    "",
    "no intervention",
    "this study does not involve any interventions",
    "women with polycystic ovary syndrome",
    "incidence",
}
RELEVANCE_PATTERNS = (
    "polycystic ovary syndrome",
    "polycystic ovarian syndrome",
    "pcos",
    "sop ",
    " sop",
    "stein-leventhal",
)
# Años claramente inválidos: OpenAlex devuelve 1970 cuando no tiene fecha
MIN_VALID_YEAR = 1990


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() != "[]"
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _normalize_doi(value: Any) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    text = text.lower()
    text = text.removeprefix("https://doi.org/")
    text = text.removeprefix("http://doi.org/")
    text = text.removeprefix("doi:")
    return text.strip(" /") or None


def _normalize_title(value: Any) -> str:
    text = (_clean_text(value) or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_relevant_to_pcos(title: Any) -> bool:
    normalized = _normalize_title(title)
    if not normalized:
        return False
    return any(pattern in normalized for pattern in RELEVANCE_PATTERNS)


def _parse_year(row: pd.Series) -> float | None:
    """Parsea el año de publicación. Descarta años claramente inválidos (< MIN_VALID_YEAR)."""
    for key in ("year", "pubdate"):
        if key in row and pd.notna(row.get(key)):
            parsed = pd.to_datetime(row.get(key), errors="coerce")
            if pd.notna(parsed):
                y = float(parsed.year)
                return y if y >= MIN_VALID_YEAR else None
            try:
                y = float(row.get(key))
                return y if y >= MIN_VALID_YEAR else None
            except Exception:
                continue
    return None


def _evidence_score(row: pd.Series) -> int:
    """
    Score de evidencia basado únicamente en datos objetivos:
    citaciones, completitud de metadatos y año.
    NO usa heurísticas de study_type — eso lo asignará el LLM.
    """
    base = 20  # base neutral para todos los artículos

    citation_value = pd.to_numeric(row.get("cited_by_count"), errors="coerce")
    citation_bonus = min(int(0 if pd.isna(citation_value) else citation_value) // 25, 20)

    completeness_bonus = sum(
        1 for field in ("doi", "journal", "year", "authors", "url", "abstract_text")
        if _has_value(row.get(field))
    )

    year = pd.to_numeric(row.get("year"), errors="coerce")
    recency_bonus = min(max(int(year) - 2010, 0), 10) if pd.notna(year) else 0

    return max(0, min(100, base + citation_bonus + completeness_bonus + recency_bonus))


def _summarize_article(row: pd.Series) -> str:
    """Resumen de metadatos básicos. Sin juicios de study_type (pendiente de LLM)."""
    title = row.get("title") or "Sin titulo"
    journal = row.get("journal") or "revista no especificada"
    year = row.get("year")
    year_text = f" ({int(year)})" if pd.notna(year) else ""
    cited = pd.to_numeric(row.get("cited_by_count"), errors="coerce")
    cited_text = f" Citado {int(cited)} veces." if pd.notna(cited) and cited > 0 else ""
    return (
        f"{title}. Publicado en {journal}{year_text}.{cited_text} "
        f"Clasificación pendiente de revisión LLM."
    )


def _metadata_score(row: pd.Series) -> int:
    score = SOURCE_PRIORITY.get(row.get("source") or "", 0) * 10
    for field in ("title", "doi", "journal", "year", "authors", "url"):
        if _has_value(row.get(field)):
            score += 1
    return score


def _first_non_null(values: pd.Series) -> Any:
    for value in values:
        if _has_value(value):
            return value
    return None


def _merge_articles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    sorted_df = df.sort_values(
        by=["canonical_id", "metadata_score", "source_priority", "cited_by_count"],
        ascending=[True, False, False, False],
    )

    merged_rows: list[dict] = []
    for canonical_id, group in sorted_df.groupby("canonical_id", sort=False):
        best = group.iloc[0].to_dict()
        merged = {"canonical_id": canonical_id}
        for column in group.columns:
            if column in {"canonical_id", "all_sources"}:
                continue
            if column == "cited_by_count":
                merged[column] = pd.to_numeric(group[column], errors="coerce").max()
            else:
                merged[column] = _first_non_null(group[column])
        merged["source"] = best.get("source")
        merged["all_sources"] = sorted(set(group["source"].dropna().astype(str).tolist()))
        merged_rows.append(merged)

    merged_df = pd.DataFrame(merged_rows)
    merged_df["source_priority"] = merged_df["source"].map(SOURCE_PRIORITY).fillna(0)
    merged_df["metadata_score"] = merged_df.apply(_metadata_score, axis=1)
    return merged_df


def _normalize_articles(pubmed_rows: list[dict], openalex_rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = pd.DataFrame(pubmed_rows + openalex_rows)
    if raw_df.empty:
        return raw_df, raw_df

    raw_df["source"] = raw_df.get("source", "unknown")
    raw_df["title"] = raw_df["title"].map(_clean_text)
    raw_df["is_relevant"] = raw_df["title"].map(_is_relevant_to_pcos)
    raw_df = raw_df[raw_df["is_relevant"]].copy()
    raw_df["doi"] = raw_df.get("doi").map(_normalize_doi)
    raw_df["normalized_title"] = raw_df["title"].map(_normalize_title)
    raw_df["canonical_id"] = raw_df["doi"].fillna("")
    raw_df.loc[raw_df["canonical_id"] == "", "canonical_id"] = raw_df["normalized_title"]
    raw_df = raw_df[raw_df["canonical_id"] != ""].copy()

    raw_df["year"] = raw_df.apply(_parse_year, axis=1)
    raw_df["journal"] = raw_df.apply(
        lambda row: _clean_text(row.get("fulljournalname")) or _clean_text(row.get("host_venue")),
        axis=1,
    )
    raw_df["abstract_text"] = raw_df.get("abstract_text")

    # study_type y evidence_tier ya no se infieren por heurística de título.
    # Se dejan como None hasta que el LLM los clasifique (tabla article_llm_labels).
    raw_df["study_type"] = None
    raw_df["evidence_tier"] = None

    raw_df["source_priority"] = raw_df["source"].map(SOURCE_PRIORITY).fillna(0)
    raw_df["metadata_score"] = raw_df.apply(_metadata_score, axis=1)
    raw_df["llm_ready"] = True

    for field in ("population", "n_total", "intervention", "comparator", "main_outcomes", "effect_direction", "limitations"):
        raw_df[field] = None

    dedup_df = _merge_articles(raw_df)
    dedup_df["evidence_score"] = dedup_df.apply(_evidence_score, axis=1)
    dedup_df["llm_ready"] = True
    dedup_df["summary_short"] = dedup_df.apply(_summarize_article, axis=1)

    ordered_columns = [
        "canonical_id", "source", "all_sources", "source_id", "doi", "title", "normalized_title", "year", "journal",
        "study_type", "evidence_tier", "evidence_score", "population", "n_total", "intervention", "comparator",
        "main_outcomes", "effect_direction", "limitations", "authors", "articleids", "pubdate", "type",
        "cited_by_count", "fulljournalname", "host_venue", "abstract_text", "url", "summary_short", "is_relevant", "llm_ready", "source_priority", "metadata_score",
    ]
    dedup_df = dedup_df.reindex(columns=ordered_columns)
    return raw_df, dedup_df


def _normalize_intervention_name(value: Any) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text if text not in NOISE_TRIAL_INTERVENTIONS else None


def _parse_listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if _clean_text(v)]
    text = _clean_text(value)
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if _clean_text(v)]
        except json.JSONDecodeError:
            pass
    return [text]


def _normalize_trials(trial_rows: list[dict]) -> pd.DataFrame:
    trials_df = pd.DataFrame(trial_rows)
    if trials_df.empty:
        return trials_df

    for list_column in ("conditions", "interventions", "outcome_measures", "linked_publications"):
        if list_column in trials_df:
            trials_df[list_column] = trials_df[list_column].map(_parse_listish)
        else:
            trials_df[list_column] = [[] for _ in range(len(trials_df))]

    trials_df["normalized_interventions"] = trials_df["interventions"].map(
        lambda items: sorted({name for name in (_normalize_intervention_name(item) for item in items) if name})
    )
    trials_df["enrollment"] = pd.to_numeric(trials_df.get("enrollment"), errors="coerce")
    return trials_df


def _serialize_objects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    for col in out.columns:
        if out[col].map(lambda x: isinstance(x, (list, dict))).any():
            out[col] = out[col].map(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
            )
    return out


def _write_brief(articles_df: pd.DataFrame) -> Path:
    brief_path = REPORTS_DIR / "latest_literature_brief.md"
    with brief_path.open("w", encoding="utf-8") as f:
        f.write("# Brief de literatura SOP\n\n")
        if articles_df.empty:
            f.write("No se encontraron articulos en la ingesta actual.\n")
            return brief_path

        top = articles_df.sort_values(by=["evidence_score", "year"], ascending=[False, False]).head(20)
        for _, row in top.iterrows():
            title = row.get("title") or "Sin titulo"
            url = row.get("url") or ""
            summary = row.get("summary_short") or ""
            f.write(f"## {title}\n")
            if url:
                f.write(f"Fuente: {url}\n\n")
            f.write(summary + "\n\n")
    return brief_path


def _write_quality_report(raw_articles_df: pd.DataFrame, articles_df: pd.DataFrame, trials_df: pd.DataFrame) -> Path:
    path = REPORTS_DIR / "data_quality_report.md"
    duplicate_count = max(len(raw_articles_df) - len(articles_df), 0)
    abstract_count = int(articles_df.get("abstract_text", pd.Series(dtype=str)).fillna("").astype(str).str.len().gt(0).sum())
    year_invalid = int((articles_df.get("year", pd.Series(dtype=float)).isna()).sum())

    lines = [
        "# Data Quality Report",
        "",
        f"- Articulos crudos tras filtro de relevancia: {len(raw_articles_df)}",
        f"- Articulos deduplicados: {len(articles_df)}",
        f"- Duplicados fusionados: {duplicate_count}",
        f"- Ensayos normalizados: {len(trials_df)}",
        f"- Articulos listos para LLM: {int(articles_df.get('llm_ready', pd.Series(dtype=bool)).fillna(False).sum())}",
        f"- Articulos con abstract: {abstract_count}",
        f"- Articulos sin año válido (filtrados): {year_invalid}",
        f"- Version de esquema LLM: {EXTRACTION_SCHEMA_VERSION}",
        "",
        "## Nota",
        "",
        "- study_type y evidence_tier no se infieren por heurística.",
        "- Se asignan mediante LLM (tabla article_llm_labels).",
        "- evidence_score se basa en: citaciones + completitud de metadatos + recencia.",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _ensure_llm_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS article_extractions (
            canonical_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            extraction_status TEXT NOT NULL,
            extractor_name TEXT,
            prompt_version TEXT,
            population TEXT,
            n_total INTEGER,
            intervention TEXT,
            comparator TEXT,
            main_outcomes TEXT,
            effect_direction TEXT,
            limitations TEXT,
            reasoning_summary TEXT,
            source_payload TEXT,
            raw_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS article_llm_labels (
            canonical_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            labeling_status TEXT NOT NULL,
            labeler_name TEXT,
            prompt_version TEXT,
            study_type_llm TEXT,
            study_type_confidence REAL,
            evidence_tier_llm TEXT,
            clinical_relevance_llm TEXT,
            mechanistic_relevance_llm TEXT,
            utility_score_llm REAL,
            llm_label_reasoning TEXT,
            source_payload TEXT,
            raw_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def build_knowledge_base() -> tuple[Path, Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    pubmed_rows = _load_jsonl(RAW_DIR / "pubmed_articles.jsonl")
    pubmed_rct_rows = _load_jsonl(RAW_DIR / "pubmed_rcts.jsonl")  # fetch dirigido a RCTs
    openalex_rows = _load_jsonl(RAW_DIR / "openalex_works.jsonl")
    trial_rows = _load_jsonl(RAW_DIR / "clinical_trials.jsonl")

    all_pubmed_rows = pubmed_rows + pubmed_rct_rows
    print(f"  PubMed general: {len(pubmed_rows)} | RCTs: {len(pubmed_rct_rows)} | OpenAlex: {len(openalex_rows)}")

    raw_articles_df, articles_df = _normalize_articles(all_pubmed_rows, openalex_rows)
    trials_df = _normalize_trials(trial_rows)

    articles_sql = _serialize_objects(articles_df)
    raw_articles_sql = _serialize_objects(raw_articles_df)
    trials_sql = _serialize_objects(trials_df)

    db_path = PROCESSED_DIR / "pcos_research.db"
    with sqlite3.connect(db_path, timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        if not raw_articles_sql.empty:
            raw_articles_sql.to_sql("raw_articles", conn, if_exists="replace", index=False)
        if not articles_sql.empty:
            articles_sql.to_sql("articles", conn, if_exists="replace", index=False)
        if not trials_sql.empty:
            trials_sql.to_sql("trials", conn, if_exists="replace", index=False)
        _ensure_llm_tables(conn)

    trials_pickle = PROCESSED_DIR / "pcos_trials.pkl"
    trials_df.to_pickle(trials_pickle)

    _write_brief(articles_df)
    _write_quality_report(raw_articles_df, articles_df, trials_df)
    return db_path, trials_pickle


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()

    db_path, pkl_path = build_knowledge_base()
    print(f"Knowledge base DB: {db_path}")
    print(f"Trials pickle: {pkl_path}")
