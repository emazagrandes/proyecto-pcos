"""Waits for PMC fulltext fetch to finish, then runs the full pipeline through anomaly_scan_v2."""

import sqlite3
import subprocess
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH   = Path("data/processed/pcos_research.db")
SCRIPTS   = Path("scripts")
PYTHON    = sys.executable


def db_count(query: str) -> int:
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        result = conn.execute(query).fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def run_step(name: str, cmd: list[str]) -> bool:
    log.info("=" * 60)
    log.info("STEP: %s", name)
    log.info("CMD:  %s", " ".join(cmd))
    log.info("=" * 60)
    result = subprocess.run(cmd, cwd=str(Path.cwd()))
    if result.returncode != 0:
        log.error("STEP FAILED: %s (exit code %d)", name, result.returncode)
        return False
    log.info("STEP DONE: %s", name)
    return True


# Step 1: Wait for PMC fulltext fetch to complete

log.info("Waiting for fetch_pmc_fulltext.py to complete...")
while True:
    total_pmc = db_count("SELECT COUNT(*) FROM articles WHERE articleids LIKE '%\"pmc\"%'")
    done      = db_count("SELECT COUNT(*) FROM article_fulltexts")
    if total_pmc > 0 and done >= total_pmc * 0.95:  # 95% done (rest are errors/no_oa)
        log.info("PMC fetch complete: %d/%d articles fetched", done, total_pmc)
        break
    log.info("PMC fetch progress: %d/%d — waiting 90s...", done, total_pmc)
    time.sleep(90)


# Step 2: Fetch non-PMC articles (Europe PMC + Semantic Scholar)

run_step(
    "fetch_nonpmc_fulltext (Europe PMC cascade)",
    [PYTHON, str(SCRIPTS / "fetch_nonpmc_fulltext.py")],
)


# Step 3: Run LLM extraction with fulltext + schema v1.3 (mechanisms)

# 3a. New articles (skip already extracted)
run_step(
    "run_ollama_extraction (new articles, top 2000)",
    [PYTHON, str(SCRIPTS / "run_ollama_extraction.py"), "--top-k", "2000"],
)

# 3b. Repopulate population sub-fields for articles with NULL bmi/ethnicity
run_step(
    "run_ollama_extraction --repopulate-pop-fields",
    [PYTHON, str(SCRIPTS / "run_ollama_extraction.py"),
     "--repopulate-pop-fields", "--top-k", "1000"],
)


# Step 4: Entity normalizer (on rich extractions)

run_step(
    "entity_normalizer",
    [PYTHON, str(SCRIPTS / "entity_normalizer.py")],
)


# Step 5: Anomaly scan (KG already populated by extraction step)

run_step(
    "anomaly_scan_v2",
    [PYTHON, str(SCRIPTS / "anomaly_scan_v2.py")],
)


# Summary

log.info("=" * 60)
log.info("PIPELINE COMPLETE")
extractions = db_count("SELECT COUNT(*) FROM article_extractions WHERE extraction_status='ollama_generated'")
kg_links    = db_count("SELECT COUNT(*) FROM mechanism_links")
entities    = db_count("SELECT COUNT(*) FROM entity")
log.info("  Extractions:     %d", extractions)
log.info("  KG triples:      %d", kg_links)
log.info("  Entities:        %d", entities)
log.info("  Reports in:      reports/")
log.info("=" * 60)
