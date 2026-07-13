#!/usr/bin/env python3
"""
Targeted re-fetch of PMC full text for rows ALREADY present in article_fulltexts.

Why this exists (2026-07): the old fetch caps chopped Results at 2000 chars,
which starved the extractor and drove the 82% 'unclear' rate. After raising the
caps in fetch_pmc_fulltext.py, the 4,300 rows already stored still hold the
truncated text. This script re-pulls the PMC XML and UPDATES those rows in place
with the now-untruncated sections.

Design choices:
  - Only touches rows with fetch_source='pmc' AND fetch_status='ok' AND a pmcid.
    Non-OA markers, errors, and semantic_scholar/abstract_only rows are left alone.
  - UPDATE in place (never DELETE) so no coverage is lost if a re-fetch fails.
  - --limit for trial→check→scale. --only-truncated to target just the rows whose
    results_text is exactly at the old 2000 cap (the ones that actually gained).
  - --order-by-unclear pulls rows whose extraction came out 'unclear' first,
    since those are where recovered Results text has the most value.
  - Reuses fetch_pmc() and parse_pmc_xml() from fetch_pmc_fulltext.py so there is
    a single source of truth for parsing + caps.

Usage:
  python scripts/refetch_pmc_fulltext.py --limit 10          # trial
  python scripts/refetch_pmc_fulltext.py --limit 100 --order-by-unclear
  python scripts/refetch_pmc_fulltext.py                     # all pmc-ok rows
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_pmc_fulltext as fp  # same dir; provides fetch_pmc, DB_PATH, RATE_DELAY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("refetch_pmc")

DB_PATH = fp.DB_PATH
RATE_DELAY = getattr(fp, "RATE_DELAY", 0.34)


def run(limit: int | None, only_truncated: bool, order_by_unclear: bool,
        dry_run: bool) -> None:
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    where = ["ft.fetch_source = 'pmc'", "ft.fetch_status = 'ok'",
             "ft.pmcid IS NOT NULL", "ft.pmcid != ''"]
    if only_truncated:
        # Rows at (or beyond) the old 2000 cap on any section — the ones that gained.
        where.append("(LENGTH(ft.results_text) >= 2000 OR "
                     "LENGTH(ft.methods_text) >= 3000 OR "
                     "LENGTH(ft.discussion_text) >= 1500)")
    where_sql = " AND ".join(where)

    order_sql = ""
    if order_by_unclear:
        # Prioritise rows whose current extraction is 'unclear'.
        order_sql = ("ORDER BY CASE WHEN ax.effect_direction = 'unclear' "
                     "THEN 0 ELSE 1 END, ft.canonical_id")

    query = f"""
        SELECT ft.canonical_id, ft.pmcid,
               LENGTH(COALESCE(ft.results_text,'')) AS old_results_len
        FROM article_fulltexts ft
        LEFT JOIN article_extractions ax ON ax.canonical_id = ft.canonical_id
        WHERE {where_sql}
        {order_sql}
    """
    work = conn.execute(query).fetchall()
    if limit:
        work = work[:limit]

    log.info("Rows to re-fetch: %d (only_truncated=%s, order_by_unclear=%s, dry_run=%s)",
             len(work), only_truncated, order_by_unclear, dry_run)

    ok = fail = grew = 0
    total_old = total_new = 0

    for i, (canonical_id, pmcid, old_len) in enumerate(work):
        if i % 50 == 0 and i > 0 and not dry_run:
            conn.commit()
            log.info("Progress %d/%d | ok=%d grew=%d fail=%d", i, len(work), ok, grew, fail)

        sections = fp.fetch_pmc(pmcid)
        if not sections or sections.get("_status") or sections.get("results_text") is None \
                and sections.get("methods_text") is None:
            fail += 1
            log.warning("PMC%s (%s): re-fetch failed / no sections", pmcid, canonical_id)
            time.sleep(RATE_DELAY)
            continue

        new_len = len(sections.get("results_text") or "")
        total_old += old_len
        total_new += new_len
        if new_len > old_len:
            grew += 1
        ok += 1

        if not dry_run:
            conn.execute("""
                UPDATE article_fulltexts
                   SET abstract_full   = ?,
                       methods_text    = ?,
                       results_text    = ?,
                       discussion_text = ?,
                       fetch_status    = 'ok',
                       fetched_at      = CURRENT_TIMESTAMP
                 WHERE canonical_id = ?
            """, (
                sections.get("abstract_full"),
                sections.get("methods_text"),
                sections.get("results_text"),
                sections.get("discussion_text"),
                canonical_id,
            ))
        time.sleep(RATE_DELAY)

    if not dry_run:
        conn.commit()

    avg_old = total_old / ok if ok else 0
    avg_new = total_new / ok if ok else 0
    log.info("Done. re-fetched ok=%d | results grew in %d | failed=%d", ok, grew, fail)
    log.info("Avg results_text length: %.0f -> %.0f chars (x%.1f)",
             avg_old, avg_new, (avg_new / avg_old) if avg_old else 0)
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-truncated", action="store_true",
                    help="Only rows at/over the old caps (the ones that gain).")
    ap.add_argument("--order-by-unclear", action="store_true",
                    help="Re-fetch 'unclear' extractions first.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Fetch and measure, but do not write to the DB.")
    args = ap.parse_args()
    run(args.limit, args.only_truncated, args.order_by_unclear, args.dry_run)
