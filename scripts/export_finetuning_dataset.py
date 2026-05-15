import argparse
import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from config import PROCESSED_DIR, REPORTS_DIR
from llm_support import EXTRACTION_SCHEMA_VERSION


DEFAULT_STATUSES = ["codex_high_confidence", "proposed_by_codex"]
DEFAULT_VAL_FRACTION = 0.2
DEFAULT_RANDOM_SEED = 42
PROMPT_VERSION = "article-label-v2-guided"
MAX_ABSTRACT_CHARS = 700


def _trim_text(value: Any, limit: int) -> str | None:
    if value in (None, "", "[]"):
        return None
    text = str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


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


def _build_prompt(row: dict[str, Any]) -> str:
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


def _load_gold_rows(conn: sqlite3.Connection, statuses: list[str]) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in statuses)
    query = f"""
        SELECT
            g.canonical_id,
            g.review_status,
            g.gold_study_type,
            g.gold_evidence_tier,
            g.gold_clinical_relevance,
            g.gold_mechanistic_relevance,
            g.gold_utility_score,
            g.review_notes,
            a.title,
            a.journal,
            a.year,
            a.abstract_text,
            a.url
        FROM article_gold_labels g
        JOIN articles a ON a.canonical_id = g.canonical_id
        WHERE g.review_status IN ({placeholders})
          AND g.gold_study_type IS NOT NULL
          AND g.gold_evidence_tier IS NOT NULL
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, statuses).fetchall()
    return [dict(row) for row in rows]


def _assistant_output(row: dict[str, Any]) -> dict[str, Any]:
    utility = row.get("gold_utility_score")
    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "canonical_id": row.get("canonical_id"),
        "study_type_llm": row.get("gold_study_type"),
        "study_type_confidence": 1.0 if row.get("review_status") == "codex_high_confidence" else 0.8,
        "evidence_tier_llm": row.get("gold_evidence_tier"),
        "clinical_relevance_llm": row.get("gold_clinical_relevance"),
        "mechanistic_relevance_llm": row.get("gold_mechanistic_relevance"),
        "utility_score_llm": float(utility) if utility not in (None, "") else None,
        "llm_label_reasoning": row.get("review_notes"),
    }


def _assign_split(rows: list[dict[str, Any]], val_fraction: float, random_seed: int) -> list[dict[str, Any]]:
    if not rows:
        return rows

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = str(row.get("review_status") or "")
        grouped.setdefault(key, []).append(dict(row))

    rng = random.Random(random_seed)
    assigned: list[dict[str, Any]] = []
    for group in grouped.values():
        rng.shuffle(group)
        n_val = max(1, int(round(len(group) * val_fraction))) if len(group) > 1 else 0
        cutoff = len(group) - n_val
        for idx, row in enumerate(group):
            row["split"] = "val" if n_val > 0 and idx >= cutoff else "train"
            assigned.append(row)
    return assigned


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_finetuning_dataset(statuses: list[str], val_fraction: float, random_seed: int) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROCESSED_DIR / "pcos_research.db"
    chat_path = PROCESSED_DIR / "fine_tuning_article_labels_chat.jsonl"
    records_path = PROCESSED_DIR / "fine_tuning_article_labels_records.jsonl"
    train_chat_path = PROCESSED_DIR / "fine_tuning_article_labels_train_chat.jsonl"
    val_chat_path = PROCESSED_DIR / "fine_tuning_article_labels_val_chat.jsonl"
    train_records_path = PROCESSED_DIR / "fine_tuning_article_labels_train_records.jsonl"
    val_records_path = PROCESSED_DIR / "fine_tuning_article_labels_val_records.jsonl"
    report_path = REPORTS_DIR / "fine_tuning_dataset_report.md"

    if not db_path.exists():
        for empty_path in (chat_path, records_path, train_chat_path, val_chat_path, train_records_path, val_records_path):
            empty_path.write_text("", encoding="utf-8")
        report_path.write_text("# Fine-tuning Dataset Report\n\nNo database found.\n", encoding="utf-8")
        return chat_path, records_path, train_chat_path, val_chat_path, train_records_path, val_records_path, report_path

    with sqlite3.connect(db_path) as conn:
        rows = _load_gold_rows(conn, statuses)

    rows = _assign_split(rows, val_fraction=val_fraction, random_seed=random_seed)

    chat_examples: list[dict[str, Any]] = []
    record_examples: list[dict[str, Any]] = []
    for row in rows:
        prompt = _build_prompt(row)
        assistant = _assistant_output(row)
        chat_examples.append(
            {
                "messages": [
                    {"role": "system", "content": "You classify biomedical articles into compact JSON labels."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
                ]
            }
        )
        record_examples.append(
            {
                "canonical_id": row.get("canonical_id"),
                "review_status": row.get("review_status"),
                "split": row.get("split"),
                "prompt_version": PROMPT_VERSION,
                "prompt": prompt,
                "target": assistant,
                "metadata": {
                    "title": row.get("title"),
                    "journal": row.get("journal"),
                    "year": row.get("year"),
                    "url": row.get("url"),
                },
            }
        )

    _write_jsonl(chat_path, chat_examples)
    _write_jsonl(records_path, record_examples)

    train_chat = [ex for ex, row in zip(chat_examples, rows) if row.get("split") == "train"]
    val_chat = [ex for ex, row in zip(chat_examples, rows) if row.get("split") == "val"]
    train_records = [ex for ex in record_examples if ex.get("split") == "train"]
    val_records = [ex for ex in record_examples if ex.get("split") == "val"]

    _write_jsonl(train_chat_path, train_chat)
    _write_jsonl(val_chat_path, val_chat)
    _write_jsonl(train_records_path, train_records)
    _write_jsonl(val_records_path, val_records)

    status_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    for row in rows:
        status_key = str(row.get("review_status") or "")
        split_key = str(row.get("split") or "")
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        split_counts[split_key] = split_counts.get(split_key, 0) + 1

    lines = [
        "# Fine-tuning Dataset Report",
        "",
        f"- Ejemplos exportados: {len(rows)}",
        f"- Prompt version: {PROMPT_VERSION}",
        f"- Estados incluidos: {', '.join(statuses)}",
        f"- Distribucion por estado: {status_counts}",
        f"- Distribucion por split: {split_counts}",
        f"- Dataset chat JSONL: {chat_path}",
        f"- Dataset records JSONL: {records_path}",
        f"- Train chat JSONL: {train_chat_path}",
        f"- Val chat JSONL: {val_chat_path}",
        f"- Train records JSONL: {train_records_path}",
        f"- Val records JSONL: {val_records_path}",
        "",
        "## Notas",
        "",
        "- El dataset chat JSONL sirve para pipelines de fine-tuning basados en mensajes.",
        "- El dataset records JSONL conserva prompt, target y metadata para auditoria y conversion futura.",
        "- `study_type_confidence` se fija en 1.0 para `codex_high_confidence` y 0.8 para `proposed_by_codex`.",
        f"- Split reproducible con val_fraction={val_fraction} y random_seed={random_seed}.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return chat_path, records_path, train_chat_path, val_chat_path, train_records_path, val_records_path, report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--statuses", nargs="*", default=DEFAULT_STATUSES)
    parser.add_argument("--val-fraction", type=float, default=DEFAULT_VAL_FRACTION)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args()

    paths = export_finetuning_dataset(args.statuses, val_fraction=args.val_fraction, random_seed=args.random_seed)
    labels = ["Chat dataset", "Records dataset", "Train chat dataset", "Val chat dataset", "Train records dataset", "Val records dataset", "Dataset report"]
    for label, value in zip(labels, paths):
        print(f"{label}: {value}")
