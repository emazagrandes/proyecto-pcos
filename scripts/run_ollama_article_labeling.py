import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from config import PROCESSED_DIR, REPORTS_DIR
from llm_support import EXTRACTION_SCHEMA_VERSION


DEFAULT_TOP_K = 10
DEFAULT_MODEL = "gemma4:31b-cloud"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
LABELER_PREFIX = "ollama_labeler"
PROMPT_VERSION = "article-label-v2-guided"
MAX_ABSTRACT_CHARS = 700
VALID_STUDY_TYPES = {
    "guideline", "meta-analysis", "rct_or_trial", "cohort", "review", "protocol", "preclinical", "case_report", "other"
}
VALID_TIERS = {"tier_1", "tier_2", "tier_3", "tier_4"}
VALID_LEVELS = {"high", "medium", "low"}


def _trim_text(value: Any, limit: int) -> str | None:
    if value in (None, "", "[]"):
        return None
    text = str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _load_candidates(conn: sqlite3.Connection, top_k: int, min_year: int | None = None) -> pd.DataFrame:
    # NOT IN (...) excluye artículos que ya tienen etiqueta exitosa.
    # Así el script es idempotente: relanzarlo no reprocesa lo ya hecho.
    # min_year permite priorizar artículos recientes (ej: RCTs de 2020+)
    year_filter = f"AND year >= {min_year}" if min_year else ""
    query = f"""
        SELECT canonical_id, title, journal, year, study_type, evidence_tier, evidence_score,
               abstract_text
        FROM articles
        WHERE llm_ready = 1
          {year_filter}
          AND canonical_id NOT IN (
              SELECT canonical_id FROM article_llm_labels
              WHERE labeling_status = 'ollama_labeled'
          )
        ORDER BY year DESC, evidence_score DESC
        LIMIT ?
    """
    return pd.read_sql_query(query, conn, params=(top_k,))


def _label_template(canonical_id: str | None) -> dict[str, Any]:
    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "canonical_id": canonical_id,
        "study_type_llm": None,
        "study_type_confidence": None,
        "evidence_tier_llm": None,
        "clinical_relevance_llm": None,
        "mechanistic_relevance_llm": None,
        "utility_score_llm": None,
        "llm_label_reasoning": None,
    }


def _build_prompt(row: pd.Series) -> str:
    template = _label_template(row.get("canonical_id"))
    abstract_text = _trim_text(row.get("abstract_text"), MAX_ABSTRACT_CHARS)
    parts = [
        f"Title: {row.get('title')}",
        f"Journal: {row.get('journal')}",
        f"Year: {row.get('year')}",
    ]
    if abstract_text:
        parts.append(f"Abstract: {abstract_text}")

    return (
        "Return JSON only. Choose the most likely study design and usefulness for PCOS research. "
        "Allowed study_type_llm: guideline, meta-analysis, rct_or_trial, cohort, review, protocol, preclinical, case_report, other. "
        "Allowed evidence_tier_llm: tier_1, tier_2, tier_3, tier_4. "
        "Allowed clinical_relevance_llm and mechanistic_relevance_llm: high, medium, low. "
        "utility_score_llm must be 0-100. Keep llm_label_reasoning under 18 words.\n\n"
        "Study type hints:\n"
        "- guideline: formal guideline, consensus statement, expert recommendation, practice recommendation.\n"
        "- meta-analysis: systematic review with pooled quantitative analysis, diagnostic meta-analysis.\n"
        "- review: narrative review or summary of existing guidelines/reviews, no original cohort/trial.\n"
        "- rct_or_trial: interventional clinical trial, randomized or non-randomized.\n"
        "- cohort: observational cohort, retrospective cohort, cross-sectional human study, survey study.\n"
        "- protocol: study protocol without outcomes.\n"
        "- preclinical: animal, cell, in vitro, or non-human mechanistic work.\n"
        "- case_report: one patient or a very small anecdotal case series.\n"
        "- other: methodology, database coverage, evaluation of LLMs/search systems, editorial, commentary.\n\n"
        "Tier hints:\n"
        "- tier_1: guideline/consensus, meta-analysis, robust clinical trial.\n"
        "- tier_2: good cohort or strong human mechanistic study.\n"
        "- tier_3: small or retrospective observational study, survey-heavy study.\n"
        "- tier_4: methodology, opinion, editorial, hypothesis, case report, weak indirect evidence.\n\n"
        "Mini examples:\n"
        "- 'Delphi consensus on diagnostic criteria' -> guideline, tier_1.\n"
        "- 'systematic review and diagnostic meta-analysis' -> meta-analysis, tier_1.\n"
        "- 'retrospective cohort and survey study' -> cohort, tier_3.\n"
        "- 'evaluation of ChatGPT/Gemini using guideline questions' -> other, tier_4.\n"
        "- 'database coverage for living guideline surveillance' -> other, tier_4.\n\n"
        "Schema:\n"
        f"{json.dumps(template, ensure_ascii=False)}\n\n"
        "Article:\n"
        + "\n".join(parts)
    )


def _strip_markdown_json(text: str) -> str:
    """Elimina bloques de markdown (```json ... ```) que algunos modelos añaden.

    Los LLMs a veces devuelven el JSON envuelto en formato markdown aunque se les
    pida JSON puro. Esta función limpia esa envoltura antes de parsear.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Quita la primera línea (```json o ```)
        lines = lines[1:]
        # Quita la última línea si es el cierre ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _chat(model: str, system: str, user: str, timeout_s: int, num_predict: int) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": num_predict,
            "num_ctx": 1536,
        },
    }
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    body = resp.json()
    content = ((body.get("message") or {}).get("content") or "").strip()
    return _strip_markdown_json(content)


def _parse_or_repair_json(model: str, content: str, timeout_s: int) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        repair_prompt = (
            "Repair this malformed JSON and return valid JSON only. Keep keys and values as faithful as possible.\n\n"
            f"Broken JSON:\n{content}"
        )
        repaired = _chat(
            model=model,
            system="You repair malformed JSON.",
            user=repair_prompt,
            timeout_s=timeout_s,
            num_predict=220,
        )
        return json.loads(repaired)


def _call_ollama(model: str, prompt: str, timeout_s: int) -> tuple[dict[str, Any], str]:
    content = _chat(
        model=model,
        system="You classify biomedical articles into compact JSON labels.",
        user=prompt,
        timeout_s=timeout_s,
        num_predict=220,
    )
    parsed = _parse_or_repair_json(model=model, content=content, timeout_s=timeout_s)
    return parsed, content


def _normalize_label_response(canonical_id: str, response: dict[str, Any]) -> dict[str, Any]:
    record = _label_template(canonical_id)
    for key in record.keys():
        if key in response:
            record[key] = response[key]
    record["schema_version"] = EXTRACTION_SCHEMA_VERSION
    record["canonical_id"] = canonical_id
    if record.get("study_type_llm") not in VALID_STUDY_TYPES:
        record["study_type_llm"] = "other"
    if record.get("evidence_tier_llm") not in VALID_TIERS:
        record["evidence_tier_llm"] = "tier_4"
    if record.get("clinical_relevance_llm") not in VALID_LEVELS:
        record["clinical_relevance_llm"] = "low"
    if record.get("mechanistic_relevance_llm") not in VALID_LEVELS:
        record["mechanistic_relevance_llm"] = "low"
    try:
        confidence = float(record.get("study_type_confidence"))
        record["study_type_confidence"] = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        record["study_type_confidence"] = None
    try:
        utility = float(record.get("utility_score_llm"))
        record["utility_score_llm"] = max(0.0, min(100.0, utility))
    except (TypeError, ValueError):
        record["utility_score_llm"] = None
    return record


def _fallback_label(canonical_id: str, error_message: str) -> dict[str, Any]:
    record = _label_template(canonical_id)
    record["study_type_llm"] = "other"
    record["evidence_tier_llm"] = "tier_4"
    record["clinical_relevance_llm"] = "low"
    record["mechanistic_relevance_llm"] = "low"
    record["utility_score_llm"] = 0.0
    record["llm_label_reasoning"] = f"LLM labeling failed: {error_message[:120]}"
    return record


def _upsert_label(conn: sqlite3.Connection, label: dict[str, Any], source_payload: dict[str, Any], raw_response: str, model: str, status: str) -> None:
    conn.execute(
        """
        INSERT INTO article_llm_labels (
            canonical_id, schema_version, labeling_status, labeler_name, prompt_version,
            study_type_llm, study_type_confidence, evidence_tier_llm, clinical_relevance_llm,
            mechanistic_relevance_llm, utility_score_llm, llm_label_reasoning,
            source_payload, raw_response, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_id) DO UPDATE SET
            schema_version=excluded.schema_version,
            labeling_status=excluded.labeling_status,
            labeler_name=excluded.labeler_name,
            prompt_version=excluded.prompt_version,
            study_type_llm=excluded.study_type_llm,
            study_type_confidence=excluded.study_type_confidence,
            evidence_tier_llm=excluded.evidence_tier_llm,
            clinical_relevance_llm=excluded.clinical_relevance_llm,
            mechanistic_relevance_llm=excluded.mechanistic_relevance_llm,
            utility_score_llm=excluded.utility_score_llm,
            llm_label_reasoning=excluded.llm_label_reasoning,
            source_payload=excluded.source_payload,
            raw_response=excluded.raw_response,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            label["canonical_id"],
            label["schema_version"],
            status,
            f"{LABELER_PREFIX}_{model}",
            PROMPT_VERSION,
            label.get("study_type_llm"),
            label.get("study_type_confidence"),
            label.get("evidence_tier_llm"),
            label.get("clinical_relevance_llm"),
            label.get("mechanistic_relevance_llm"),
            label.get("utility_score_llm"),
            label.get("llm_label_reasoning"),
            json.dumps(source_payload, ensure_ascii=False),
            raw_response,
        ),
    )


def _write_report(results: list[dict[str, Any]], model: str, dry_run: bool) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "ollama_labeling_report.md"
    df = pd.DataFrame(results)
    lines = [
        "# Ollama Labeling Report",
        "",
        f"- Model: {model}",
        f"- Dry run: {dry_run}",
        f"- Prompt version: {PROMPT_VERSION}",
        f"- Registros procesados: {len(results)}",
        "",
    ]
    if not df.empty:
        lines.extend(["## Distribucion", ""])
        for field in ("study_type_llm", "evidence_tier_llm", "clinical_relevance_llm"):
            lines.append(f"### {field}")
            counts = df[field].fillna("null").value_counts().to_dict()
            for key, value in counts.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
    lines.extend(["## Ejemplos", ""])
    for record in results[:5]:
        lines.append(f"### {record['canonical_id']}")
        lines.append(f"- study_type_llm: {record.get('study_type_llm')}")
        lines.append(f"- evidence_tier_llm: {record.get('evidence_tier_llm')}")
        lines.append(f"- clinical_relevance_llm: {record.get('clinical_relevance_llm')}")
        lines.append(f"- utility_score_llm: {record.get('utility_score_llm')}")
        lines.append(f"- llm_label_reasoning: {record.get('llm_label_reasoning')}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_ollama_labeling(top_k: int, model: str, timeout_s: int, dry_run: bool,
                        min_year: int | None = None) -> tuple[Path, Path]:
    db_path = PROCESSED_DIR / "pcos_research.db"
    out_path = PROCESSED_DIR / "ollama_article_labels.jsonl"
    if not db_path.exists():
        out_path.write_text("", encoding="utf-8")
        report_path = _write_report([], model, dry_run)
        return out_path, report_path

    with sqlite3.connect(db_path, timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        articles = _load_candidates(conn, top_k=top_k, min_year=min_year)
        results: list[dict[str, Any]] = []
        for _, row in articles.iterrows():
            source_payload = row.to_dict()
            canonical_id = source_payload["canonical_id"]
            if dry_run:
                label = _label_template(canonical_id)
                label["llm_label_reasoning"] = "Dry run: prompt generated but model not called."
                raw_response = json.dumps(label, ensure_ascii=False)
                status = "ollama_label_dry_run"
            else:
                try:
                    prompt = _build_prompt(row)
                    parsed, raw_response = _call_ollama(model=model, prompt=prompt, timeout_s=timeout_s)
                    label = _normalize_label_response(canonical_id, parsed)
                    status = "ollama_labeled"
                except Exception as exc:
                    raw_response = str(exc)
                    label = _fallback_label(canonical_id, str(exc))
                    status = "ollama_label_failed"
            _upsert_label(conn, label, source_payload, raw_response, model, status)
            results.append(label)
        conn.commit()

    with out_path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report_path = _write_report(results, model, dry_run)
    return out_path, report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-s", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-year", type=int, default=None,
                        help="Priorizar articulos desde este ano (ej: 2020 para RCTs recientes)")
    args = parser.parse_args()

    data_path, report_path = run_ollama_labeling(
        top_k=args.top_k,
        model=args.model,
        timeout_s=args.timeout_s,
        dry_run=args.dry_run,
        min_year=args.min_year,
    )
    print(f"Ollama labels: {data_path}")
    print(f"Ollama labeling report: {report_path}")
