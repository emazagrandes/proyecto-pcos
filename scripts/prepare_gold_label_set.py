import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


DEFAULT_TOP_K = 30
REVIEW_FIELDS = [
    "gold_study_type",
    "gold_evidence_tier",
    "gold_clinical_relevance",
    "gold_mechanistic_relevance",
    "gold_utility_score",
    "review_notes",
    "reviewer_id",
]


def _ensure_gold_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS article_gold_labels (
            canonical_id TEXT PRIMARY KEY,
            review_status TEXT NOT NULL,
            gold_study_type TEXT,
            gold_evidence_tier TEXT,
            gold_clinical_relevance TEXT,
            gold_mechanistic_relevance TEXT,
            gold_utility_score REAL,
            review_notes TEXT,
            reviewer_id TEXT,
            source_payload TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _load_candidates(conn: sqlite3.Connection, top_k: int) -> pd.DataFrame:
    query = """
        WITH labeled AS (
            SELECT
                a.canonical_id,
                a.title,
                a.year,
                a.journal,
                a.abstract_text,
                a.study_type,
                a.evidence_tier,
                a.evidence_score,
                l.study_type_llm,
                l.evidence_tier_llm,
                l.clinical_relevance_llm,
                l.mechanistic_relevance_llm,
                l.utility_score_llm,
                l.llm_label_reasoning,
                CASE
                    WHEN l.canonical_id IS NULL THEN 1
                    WHEN a.study_type != COALESCE(l.study_type_llm, '') THEN 1
                    WHEN a.evidence_tier != COALESCE(l.evidence_tier_llm, '') THEN 1
                    ELSE 0
                END AS disagreement_flag
            FROM articles a
            LEFT JOIN article_llm_labels l ON a.canonical_id = l.canonical_id
            WHERE a.llm_ready = 1
        )
        SELECT *
        FROM labeled
        ORDER BY disagreement_flag DESC, evidence_score DESC, year DESC
        LIMIT ?
    """
    return pd.read_sql_query(query, conn, params=(top_k,))


def _seed_gold_table(conn: sqlite3.Connection, rows: list[dict]) -> None:
    for row in rows:
        conn.execute(
            """
            INSERT INTO article_gold_labels (
                canonical_id, review_status, source_payload, updated_at
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(canonical_id) DO UPDATE SET
                source_payload=excluded.source_payload,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                row["canonical_id"],
                "pending_review",
                json.dumps(row, ensure_ascii=False),
            ),
        )


def _build_review_frame(df: pd.DataFrame) -> pd.DataFrame:
    review_df = df.copy()
    review_df["review_priority"] = review_df.apply(
        lambda row: "high" if row.get("disagreement_flag") else "medium",
        axis=1,
    )
    for field in REVIEW_FIELDS:
        review_df[field] = None
    ordered_columns = [
        "review_priority",
        "canonical_id",
        "title",
        "year",
        "journal",
        "study_type",
        "evidence_tier",
        "evidence_score",
        "study_type_llm",
        "evidence_tier_llm",
        "clinical_relevance_llm",
        "mechanistic_relevance_llm",
        "utility_score_llm",
        "llm_label_reasoning",
        "disagreement_flag",
        "abstract_text",
        *REVIEW_FIELDS,
    ]
    return review_df.reindex(columns=ordered_columns)


def _write_report(df: pd.DataFrame, out_csv: Path) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "gold_label_queue.md"
    disagreements = int(df["disagreement_flag"].fillna(0).sum()) if not df.empty else 0
    lines = [
        "# Gold Label Queue",
        "",
        f"- Articulos en cola: {len(df)}",
        f"- Conflictos heuristica vs LLM: {disagreements}",
        f"- CSV de revision: {out_csv}",
        "",
        "## Prioridades",
        "",
    ]
    if df.empty:
        lines.append("No hay articulos preparados para revision.")
    else:
        for _, row in df.head(10).iterrows():
            lines.append(f"### {row['canonical_id']}")
            lines.append(f"- review_priority: {row['review_priority']}")
            lines.append(f"- heuristica: {row['study_type']} / {row['evidence_tier']}")
            lines.append(f"- llm: {row['study_type_llm']} / {row['evidence_tier_llm']}")
            lines.append(f"- motivo_llm: {row['llm_label_reasoning']}")
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def prepare_gold_label_set(top_k: int) -> tuple[Path, Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROCESSED_DIR / "pcos_research.db"
    out_csv = PROCESSED_DIR / "gold_label_candidates.csv"
    if not db_path.exists():
        empty = pd.DataFrame()
        empty.to_csv(out_csv, index=False)
        report = _write_report(empty, out_csv)
        return out_csv, report

    with sqlite3.connect(db_path) as conn:
        _ensure_gold_table(conn)
        candidates = _load_candidates(conn, top_k=top_k)
        review_df = _build_review_frame(candidates)
        _seed_gold_table(conn, review_df.to_dict(orient="records"))
        conn.commit()

    review_df.to_csv(out_csv, index=False, encoding="utf-8")
    report = _write_report(review_df, out_csv)
    return out_csv, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    csv_path, report_path = prepare_gold_label_set(top_k=args.top_k)
    print(f"Gold label CSV: {csv_path}")
    print(f"Gold label report: {report_path}")
