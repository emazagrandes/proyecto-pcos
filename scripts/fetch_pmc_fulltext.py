"""
fetch_pmc_fulltext.py
======================
Fetches full text sections (Methods, Results, Discussion) from PubMed Central
for articles that have a PMC ID. Stores them in the article_fulltexts table.

PMC E-utilities API (free, no auth):
  https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
  db=pmc, rettype=xml → structured full text XML

Rate limit: 3 req/sec without API key, 10 req/sec with NCBI_API_KEY env var.

Run:
    python scripts/fetch_pmc_fulltext.py --limit 100
    python scripts/fetch_pmc_fulltext.py           # all pending
    python scripts/fetch_pmc_fulltext.py --reset   # re-fetch everything
"""

import json
import logging
import os
import re
import sqlite3
import time
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DB_PATH   = Path("data/processed/pcos_research.db")
BASE_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
API_KEY   = os.environ.get("NCBI_API_KEY", "")  # optional — 10 req/s vs 3 req/s
RATE_DELAY = 0.35 if API_KEY else 1.1  # seconds between requests

# ─────────────────────────────────────────────────────────────────────────────
# DB setup
# ─────────────────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS article_fulltexts (
    canonical_id    TEXT PRIMARY KEY,
    pmcid           TEXT,
    fetch_source    TEXT,   -- 'pmc' | 'europe_pmc' | 'semantic_scholar' | 'abstract_only'
    abstract_full   TEXT,   -- structured abstract (often richer than PubMed abstract)
    methods_text    TEXT,   -- Methods / Participants / Study design
    results_text    TEXT,   -- Results section
    discussion_text TEXT,   -- Discussion / Limitations
    fetch_status    TEXT DEFAULT 'ok',   -- 'ok' | 'error' | 'not_open_access'
    fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fulltexts_pmcid ON article_fulltexts(pmcid);
CREATE INDEX IF NOT EXISTS idx_fulltexts_source ON article_fulltexts(fetch_source);
"""


def init_db(conn: sqlite3.Connection) -> None:
    for stmt in [s.strip() for s in DDL.split(";") if s.strip()]:
        conn.execute(stmt)
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# PMC ID extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_pmcid(articleids_json: str) -> str | None:
    """Parse articleids JSON and return PMC ID (without 'PMC' prefix)."""
    try:
        ids = json.loads(articleids_json)
        for item in ids:
            if item.get("idtype") == "pmc":
                val = str(item["value"]).replace("PMC", "").strip()
                if val.isdigit():
                    return val
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# XML parsing: extract text from named sections
# ─────────────────────────────────────────────────────────────────────────────

# Section type keywords to match → target field
SECTION_MAP = {
    "methods_text":    {"method", "methods", "patient", "patients", "participant",
                        "participants", "study design", "study population",
                        "materials and methods", "subjects"},
    "results_text":    {"result", "results", "findings", "outcome", "outcomes"},
    "discussion_text": {"discussion", "conclusion", "conclusions", "limitations",
                        "limitation"},
    "abstract_full":   {"abstract"},
}


def _get_text(elem) -> str:
    """Recursively extract all text from an XML element."""
    parts = []
    if elem.text:
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(_get_text(child))
        if child.tail:
            parts.append(child.tail.strip())
    return " ".join(p for p in parts if p)


def _classify_section(title: str) -> str | None:
    """Return the field name for a section title, or None if not relevant."""
    t = title.lower().strip()
    for field, keywords in SECTION_MAP.items():
        if any(kw in t for kw in keywords):
            return field
    return None


def parse_pmc_xml(xml_text: str) -> dict[str, str | None]:
    """
    Parse PMC full text XML and extract key sections.
    Returns dict with keys: abstract_full, methods_text, results_text, discussion_text.
    """
    result: dict[str, list[str]] = {
        "abstract_full":   [],
        "methods_text":    [],
        "results_text":    [],
        "discussion_text": [],
    }

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        log.warning("XML parse error: %s", e)
        return {k: None for k in result}

    # Walk all <sec> elements with a <title>
    for sec in root.iter("sec"):
        title_elem = sec.find("title")
        title = _get_text(title_elem) if title_elem is not None else ""
        field = _classify_section(title) if title else None

        # Also check sec-type attribute
        if field is None:
            sec_type = sec.get("sec-type", "").lower()
            field = _classify_section(sec_type) if sec_type else None

        if field:
            # Get all paragraph text from this section
            paragraphs = []
            for p in sec.iter("p"):
                text = _get_text(p)
                if text:
                    paragraphs.append(text)
            if paragraphs:
                result[field].append(" ".join(paragraphs))

    # Also extract structured abstract
    for abstract in root.iter("abstract"):
        texts = []
        for child in abstract:
            title_elem = child.find("title")
            t = _get_text(title_elem) + ": " if title_elem is not None else ""
            for p in child.iter("p"):
                texts.append(t + _get_text(p))
        if texts:
            result["abstract_full"].append(" ".join(texts))

    # Combine and truncate each section.
    # Caps raised 2026-07: the old 2000-char results cap chopped the Results
    # section (where effect_direction/p-values/magnitude live), which was a
    # major driver of the 82% 'unclear' extraction rate. Kept generous but
    # bounded so a pathological full text can't blow up the DB/prompt.
    MAX_CHARS = {"methods_text": 12000, "results_text": 20000,
                 "discussion_text": 10000, "abstract_full": 5000}

    return {
        k: " [...] ".join(v)[:MAX_CHARS.get(k, 2000)] if v else None
        for k, v in result.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fetch from PMC API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_pmc(pmcid: str) -> dict[str, str | None] | None:
    """
    Fetch full text XML from PMC for a given PMC ID.
    Returns parsed section dict or None on error.
    """
    params = {
        "db":      "pmc",
        "id":      pmcid,
        "rettype": "xml",
        "retmode": "xml",
    }
    if API_KEY:
        params["api_key"] = API_KEY

    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        xml_text = resp.text

        # PMC returns an error XML when the article is not open access
        if "<error>" in xml_text or "cannot be found" in xml_text.lower():
            return {"_status": "not_open_access"}

        sections = parse_pmc_xml(xml_text)
        return sections

    except requests.RequestException as e:
        log.warning("PMC fetch error for PMC%s: %s", pmcid, e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run(limit: int | None, reset: bool) -> None:
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    init_db(conn)

    if reset:
        conn.execute("DELETE FROM article_fulltexts")
        conn.commit()
        log.info("Reset: cleared article_fulltexts table.")

    # Articles with PMC IDs not yet fetched
    already_fetched = {
        r[0] for r in conn.execute(
            "SELECT canonical_id FROM article_fulltexts"
        ).fetchall()
    }

    candidates = conn.execute("""
        SELECT canonical_id, articleids
        FROM articles
        WHERE articleids IS NOT NULL
          AND articleids LIKE '%"pmc"%'
        ORDER BY evidence_score DESC NULLS LAST
    """).fetchall()

    # Extract PMC IDs and filter out already fetched
    work = []
    for canonical_id, articleids_json in candidates:
        if canonical_id in already_fetched:
            continue
        pmcid = extract_pmcid(articleids_json)
        if pmcid:
            work.append((canonical_id, pmcid))

    if limit:
        work = work[:limit]

    log.info("Articles with PMC ID to fetch: %d", len(work))

    ok_count = 0
    error_count = 0
    no_oa_count = 0

    for i, (canonical_id, pmcid) in enumerate(work):
        if i % 50 == 0 and i > 0:
            conn.commit()
            log.info("Progress: %d/%d | ok=%d, no_oa=%d, errors=%d",
                     i, len(work), ok_count, no_oa_count, error_count)

        sections = fetch_pmc(pmcid)

        if sections is None:
            status = "error"
            error_count += 1
            conn.execute("""
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, pmcid, fetch_source, fetch_status)
                VALUES (?, ?, 'pmc', ?)
            """, (canonical_id, pmcid, status))

        elif sections.get("_status") == "not_open_access":
            status = "not_open_access"
            no_oa_count += 1
            conn.execute("""
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, pmcid, fetch_source, fetch_status)
                VALUES (?, ?, 'pmc', ?)
            """, (canonical_id, pmcid, status))

        else:
            status = "ok"
            ok_count += 1
            conn.execute("""
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, pmcid, fetch_source,
                     abstract_full, methods_text, results_text, discussion_text,
                     fetch_status)
                VALUES (?, ?, 'pmc', ?, ?, ?, ?, ?)
            """, (
                canonical_id, pmcid,
                sections.get("abstract_full"),
                sections.get("methods_text"),
                sections.get("results_text"),
                sections.get("discussion_text"),
                status,
            ))

        time.sleep(RATE_DELAY)

    conn.commit()

    total_stored = conn.execute(
        "SELECT COUNT(*) FROM article_fulltexts WHERE fetch_status = 'ok'"
    ).fetchone()[0]
    log.info("Done. Fetched: ok=%d | no_oa=%d | errors=%d | total ok in DB: %d",
             ok_count, no_oa_count, error_count, total_stored)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Max articles to fetch (default: all pending)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete all fetched fulltexts and re-fetch")
    args = parser.parse_args()
    run(args.limit, args.reset)
