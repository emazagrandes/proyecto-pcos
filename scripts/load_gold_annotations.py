#!/usr/bin/env python3
"""
Load human gold annotations from gold_annotation_sheet.csv into
article_gold_extractions. Idempotent (INSERT OR REPLACE by canonical_id).

The CSV is produced by the sampling step and has empty gold_* columns for the
reviewer to fill:
    gold_effect_direction  (favorable|neutral|mixed|unfavorable|unclear)
    gold_intervention
    gold_n_total
    gold_notes

Only rows where gold_effect_direction is non-empty are loaded, so a
partially-annotated sheet works fine.

Usage:
  python scripts/load_gold_annotations.py --csv gold_annotation_sheet.csv --reviewer elena
"""
from __future__ import annotations
import argparse, csv, sqlite3
from pathlib import Path

DB_PATH = Path("data/processed/pcos_research.db")
VALID = {"favorable", "neutral", "mixed", "unfavorable", "unclear"}


def run(csv_path: str, reviewer: str) -> None:
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    loaded = skipped = bad = 0
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ed = (row.get("gold_effect_direction") or "").strip().lower()
            if not ed:
                skipped += 1
                continue
            if ed not in VALID:
                print(f"  WARN invalid effect '{ed}' for {row['canonical_id']} — skipped")
                bad += 1
                continue
            n_raw = (row.get("gold_n_total") or "").strip()
            n_total = int(n_raw) if n_raw.isdigit() else None
            conn.execute("""
                INSERT OR REPLACE INTO article_gold_extractions
                    (canonical_id, gold_effect_direction, gold_intervention,
                     gold_n_total, gold_notes, reviewer_id, stratum_study_type,
                     updated_at)
                VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            """, (row["canonical_id"], ed,
                  (row.get("gold_intervention") or "").strip() or None,
                  n_total,
                  (row.get("gold_notes") or "").strip() or None,
                  reviewer,
                  (row.get("study_type_llm") or "").strip() or None))
            loaded += 1
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM article_gold_extractions").fetchone()[0]
    conn.close()
    print(f"Loaded {loaded} gold rows (skipped empty={skipped}, invalid={bad}). "
          f"Table now holds {total} gold extractions.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="gold_annotation_sheet.csv")
    ap.add_argument("--reviewer", default="human")
    args = ap.parse_args()
    run(args.csv, args.reviewer)
