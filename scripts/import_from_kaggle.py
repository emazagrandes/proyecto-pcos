"""
import_from_kaggle.py — Importa extracciones producidas por Kaggle a SQLite.

Uso:
    python scripts/import_from_kaggle.py --input data/kaggle_export/extractions_output.jsonl
"""
import argparse, json, sqlite3, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH = Path("data/processed/pcos_research.db")


def import_extractions(input_file: Path, dry_run: bool = False):
    if not input_file.exists():
        raise FileNotFoundError(input_file)

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    # Asegurar que la tabla existe con el schema v1.3
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_extractions (
            canonical_id TEXT PRIMARY KEY,
            schema_version TEXT DEFAULT '1.3',
            extraction_status TEXT DEFAULT 'ollama_generated',
            intervention TEXT, comparator TEXT, dose TEXT,
            effect_direction TEXT, n_total INTEGER,
            main_outcomes TEXT, limitations TEXT,
            population TEXT, population_diet TEXT,
            population_bmi TEXT, population_age_range TEXT,
            population_comorbidities TEXT, population_ethnicity TEXT,
            notable_finding TEXT, mechanisms TEXT,
            reasoning_summary TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    lines = input_file.read_text(encoding="utf-8").strip().split("\n")
    inserted = skipped = errors = 0

    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            log.warning("JSON parse error: %s — skipping", e)
            errors += 1
            continue

        cid = rec.get("canonical_id")
        if not cid:
            errors += 1
            continue

        # Check if already extracted
        exists = conn.execute(
            "SELECT 1 FROM article_extractions WHERE canonical_id=? AND extraction_status='ollama_generated'",
            (cid,)
        ).fetchone()

        if exists:
            skipped += 1
            continue

        if not dry_run:
            conn.execute("""
                INSERT OR REPLACE INTO article_extractions
                (canonical_id, schema_version, extraction_status,
                 intervention, comparator, dose, effect_direction, n_total,
                 main_outcomes, limitations, population,
                 population_diet, population_bmi, population_age_range,
                 population_comorbidities, population_ethnicity,
                 notable_finding, mechanisms, reasoning_summary)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                cid, rec.get("schema_version", "1.3"), "ollama_generated",
                rec.get("intervention"), rec.get("comparator"), rec.get("dose"),
                rec.get("effect_direction"), rec.get("n_total"),
                json.dumps(rec.get("main_outcomes", [])) if isinstance(rec.get("main_outcomes"), list) else rec.get("main_outcomes"),
                json.dumps(rec.get("limitations", [])) if isinstance(rec.get("limitations"), list) else rec.get("limitations"),
                rec.get("population"),
                rec.get("population_diet"), rec.get("population_bmi"),
                rec.get("population_age_range"), rec.get("population_comorbidities"),
                rec.get("population_ethnicity"),
                rec.get("notable_finding"),
                json.dumps(rec.get("mechanisms", [])) if isinstance(rec.get("mechanisms"), list) else rec.get("mechanisms"),
                rec.get("reasoning_summary"),
            ))
            inserted += 1
        else:
            log.info("DRY RUN — would insert: %s (%s)", cid, rec.get("intervention","?"))
            inserted += 1

    if not dry_run:
        conn.commit()
    conn.close()

    log.info("Done: inserted=%d  skipped=%d  errors=%d", inserted, skipped, errors)
    if dry_run:
        log.info("(DRY RUN — nothing written to DB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/kaggle_export/extractions_output.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    import_extractions(Path(args.input), args.dry_run)
