"""
fetch_nonpmc_fulltext.py
========================
Fetches supplementary text for articles WITHOUT a PMC ID.

Strategy (cascade — tries each source in order until one works):
  1. Europe PMC REST API  — broader journal coverage, free, no auth
     https://www.ebi.ac.uk/europepmc/webservices/rest/{pmid}/fullTextXML
  2. Semantic Scholar API — structured abstract sections (background/methods/results)
     https://api.semanticscholar.org/graph/v1/paper/{doi}/details
  3. abstract_only        — fallback: marks article so the extractor
                            knows only the PubMed abstract is available
                            (no new text added, but fetch_source recorded)

All results go into article_fulltexts with fetch_source identifying the origin.
Articles already in article_fulltexts (from PMC fetch) are skipped.

Run:
    python scripts/fetch_nonpmc_fulltext.py --limit 200
    python scripts/fetch_nonpmc_fulltext.py           # all pending
    python scripts/fetch_nonpmc_fulltext.py --source europepmc   # only EPMC
    python scripts/fetch_nonpmc_fulltext.py --source semanticscholar
    python scripts/fetch_nonpmc_fulltext.py --source abstract_only  # fill remaining
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

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH = Path("data/processed/pcos_research.db")

# ─────────────────────────────────────────────────────────────────────────────
# Rate limits
# ─────────────────────────────────────────────────────────────────────────────
EPMC_DELAY  = 0.5   # Europe PMC: ~2 req/s to be polite
S2_DELAY    = 1.1   # Semantic Scholar free tier: 1 req/s (100 req/5min)
S2_API_KEY  = os.environ.get("S2_API_KEY", "")  # optional — raises to 10 req/s

# ─────────────────────────────────────────────────────────────────────────────
# XML parsing helpers (shared with fetch_pmc_fulltext.py)
# ─────────────────────────────────────────────────────────────────────────────

SECTION_MAP = {
    "methods_text":    {"method", "methods", "patient", "patients", "participant",
                        "participants", "study design", "study population",
                        "materials and methods", "subjects", "inclusion"},
    "results_text":    {"result", "results", "findings", "outcome", "outcomes"},
    "discussion_text": {"discussion", "conclusion", "conclusions", "limitations",
                        "limitation"},
    "abstract_full":   {"abstract"},
}


def _get_text(elem) -> str:
    parts = []
    if elem.text:
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(_get_text(child))
        if child.tail:
            parts.append(child.tail.strip())
    return " ".join(p for p in parts if p)


def _classify_section(title: str) -> str | None:
    t = title.lower().strip()
    for field, keywords in SECTION_MAP.items():
        if any(kw in t for kw in keywords):
            return field
    return None


def _parse_pmc_xml(xml_text: str) -> dict[str, str | None]:
    """Shared XML parser — same logic as fetch_pmc_fulltext.py."""
    result: dict[str, list[str]] = {
        "abstract_full": [], "methods_text": [],
        "results_text": [], "discussion_text": [],
    }
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        log.warning("XML parse error: %s", e)
        return {k: None for k in result}

    for sec in root.iter("sec"):
        title_elem = sec.find("title")
        title = _get_text(title_elem) if title_elem is not None else ""
        field = _classify_section(title) if title else None
        if field is None:
            sec_type = sec.get("sec-type", "").lower()
            field = _classify_section(sec_type) if sec_type else None
        if field:
            paragraphs = [_get_text(p) for p in sec.iter("p") if _get_text(p)]
            if paragraphs:
                result[field].append(" ".join(paragraphs))

    for abstract in root.iter("abstract"):
        texts = []
        for child in abstract:
            title_elem = child.find("title")
            t = _get_text(title_elem) + ": " if title_elem is not None else ""
            for p in child.iter("p"):
                texts.append(t + _get_text(p))
        if texts:
            result["abstract_full"].append(" ".join(texts))

    # Caps raised 2026-07 to match fetch_pmc_fulltext.py (see note there).
    MAX_CHARS = {"methods_text": 12000, "results_text": 20000,
                 "discussion_text": 10000, "abstract_full": 5000}
    return {
        k: " [...] ".join(v)[:MAX_CHARS.get(k, 5000)] if v else None
        for k, v in result.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 1: Europe PMC
# ─────────────────────────────────────────────────────────────────────────────

def _europepmc_lookup_pmcid(pmid: str) -> "str | None":
    """
    Step 1 of Europe PMC full text retrieval: resolve a PMID to a Europe PMC
    full-text id via the search endpoint.

    Europe PMC's fullTextXML endpoint is keyed by the SOURCE id (e.g. PMCxxxxxxx
    or MED prefix), NOT by a bare PMID — a bare PMID always 404s. The search
    endpoint returns, per article, whether the full text is in Europe PMC
    (inEPMC=Y) and the id to fetch it with (fullTextIdList / pmcid). This step is
    also a coverage lever: it can discover a PMCID that PubMed's articleids never
    carried, so an article we thought was abstract-only turns out to be OA here.

    Returns a fetchable full-text id (e.g. 'PMC7399751') or None.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": f"EXT_ID:{pmid} AND SRC:MED",
              "format": "json", "resultType": "core"}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("resultList", {}).get("result", [])
        if not results:
            return None
        r0 = results[0]
        if r0.get("inEPMC") != "Y":
            return None
        ft_ids = (r0.get("fullTextIdList") or {}).get("fullTextId") or []
        if ft_ids:
            return ft_ids[0]
        pmcid = r0.get("pmcid")
        return pmcid if pmcid else None
    except (requests.RequestException, ValueError) as e:
        log.warning("EuropePMC search error for PMID %s: %s", pmid, e)
        return None


def fetch_europepmc(pmid: str) -> dict[str, str | None] | None:
    """
    Fetch full text XML from Europe PMC by PMID (two-step).

    Europe PMC covers ~5M+ open-access articles, including author manuscripts and
    many not in NCBI PMC. Retrieval is two calls:
      1. search by PMID  -> full-text id (PMCxxxxxxx) + inEPMC flag
      2. fetch PMC{id}/fullTextXML and parse sections

    Returns parsed sections, {"_status": "not_open_access"} if no OA full text,
    or None on network error.
    """
    ft_id = _europepmc_lookup_pmcid(pmid)
    if not ft_id:
        return {"_status": "not_open_access"}

    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{ft_id}/fullTextXML"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            return {"_status": "not_open_access"}
        resp.raise_for_status()
        xml_text = resp.text
        if "<error" in xml_text.lower() or "not found" in xml_text.lower():
            return {"_status": "not_open_access"}
        sections = _parse_pmc_xml(xml_text)
        if any(sections.get(k) for k in ("methods_text", "results_text", "abstract_full")):
            return sections
        return {"_status": "not_open_access"}
    except requests.RequestException as e:
        log.warning("EuropePMC error for PMID %s (ft_id=%s): %s", pmid, ft_id, e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Source 2: Semantic Scholar
# ─────────────────────────────────────────────────────────────────────────────

def fetch_semanticscholar(doi: str | None, pmid: str | None) -> dict[str, str | None] | None:
    """
    Fetch structured abstract sections from Semantic Scholar.
    Uses DOI if available, falls back to PMID.

    S2 returns `abstract` (plain) and sometimes `tldr` (machine-generated summary).
    It does NOT return Methods/Results sections in the API response.
    We map: abstract → abstract_full, tldr → prepended to abstract_full.

    For our purposes this is better than nothing when we only have the PubMed abstract,
    because S2 sometimes has slightly fuller abstracts (some journals truncate in PubMed).
    """
    if not doi and not pmid:
        return None

    paper_id = f"DOI:{doi}" if doi else f"PMID:{pmid}"
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    params = {"fields": "abstract,tldr,openAccessPdf,externalIds"}
    headers = {"x-api-key": S2_API_KEY} if S2_API_KEY else {}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code == 404:
            return {"_status": "not_open_access"}
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.warning("S2 error for %s: %s", paper_id, e)
        return None

    abstract = data.get("abstract") or ""
    tldr     = (data.get("tldr") or {}).get("text") or ""

    if not abstract and not tldr:
        return {"_status": "not_open_access"}

    # Combine TLDR + abstract as a richer abstract
    combined = ""
    if tldr:
        combined += f"[AI summary] {tldr}\n\n"
    if abstract:
        combined += abstract

    return {
        "abstract_full":   combined[:5000] if combined else None,
        "methods_text":    None,  # S2 API doesn't return section text
        "results_text":    None,
        "discussion_text": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_pmid(articleids_json: str | None) -> str | None:
    if not articleids_json:
        return None
    try:
        ids = json.loads(articleids_json)
        for item in ids:
            if item.get("idtype") == "pubmed":
                v = str(item["value"]).strip()
                if v.isdigit():
                    return v
    except Exception:
        pass
    return None


def _extract_doi(articleids_json: str | None, doi_col: str | None) -> str | None:
    """Return DOI from articles.doi column or articleids JSON."""
    if doi_col:
        return doi_col.strip()
    if not articleids_json:
        return None
    try:
        ids = json.loads(articleids_json)
        for item in ids:
            if item.get("idtype") in ("doi", "DOI"):
                return str(item["value"]).strip()
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def _db_execute_with_retry(conn: sqlite3.Connection, sql: str, params: tuple = (),
                            max_retries: int = 6) -> None:
    """Execute a write statement with retry on DB lock (exponential backoff)."""
    for attempt in range(1, max_retries + 1):
        try:
            conn.execute(sql, params)
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries:
                wait = min(2 ** attempt, 60)
                log.warning("DB locked (attempt %d/%d), retrying in %ds...", attempt, max_retries, wait)
                time.sleep(wait)
            else:
                raise


def run(limit: int | None, source_filter: str | None) -> None:
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")  # clear stale WAL before writing

    # Ensure fetch_source column exists (may be running before pmc script)
    try:
        conn.execute("ALTER TABLE article_fulltexts ADD COLUMN fetch_source TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # Articles NOT already in article_fulltexts AND without a PMC ID
    # (those with PMC ID are handled by fetch_pmc_fulltext.py)
    already_fetched = {
        r[0] for r in conn.execute("SELECT canonical_id FROM article_fulltexts").fetchall()
    }

    # Get articles without PMC ID
    candidates = conn.execute("""
        SELECT canonical_id, articleids, doi
        FROM articles
        WHERE (articleids IS NULL OR articleids NOT LIKE '%"pmc"%')
        ORDER BY evidence_score DESC NULLS LAST
    """).fetchall()

    work = []
    for canonical_id, articleids_json, doi_col in candidates:
        if canonical_id in already_fetched:
            continue
        pmid = _extract_pmid(articleids_json)
        doi  = _extract_doi(articleids_json, doi_col)
        work.append((canonical_id, pmid, doi))

    if limit:
        work = work[:limit]

    log.info("Articles without PMC ID to fetch: %d", len(work))

    counters = {"ok_epmc": 0, "ok_s2": 0, "ok_abstract": 0,
                "not_oa": 0, "error": 0}

    for i, (canonical_id, pmid, doi) in enumerate(work):
        if i % 50 == 0 and i > 0:
            conn.commit()
            log.info("Progress: %d/%d | %s", i, len(work), counters)

        sections = None
        fetch_source = None

        # ── Source 1: Europe PMC (needs PMID) ────────────────────────────────
        if pmid and source_filter in (None, "europepmc"):
            sections = fetch_europepmc(pmid)
            time.sleep(EPMC_DELAY)
            if sections and sections.get("_status") != "not_open_access" and sections is not None:
                fetch_source = "europe_pmc"

        # ── Source 2: Semantic Scholar (needs DOI or PMID) ───────────────────
        if fetch_source is None and source_filter in (None, "semanticscholar"):
            sections = fetch_semanticscholar(doi, pmid)
            time.sleep(S2_DELAY)
            if sections and sections.get("_status") != "not_open_access" and sections is not None:
                fetch_source = "semantic_scholar"

        # ── Fallback: mark as abstract_only ──────────────────────────────────
        if fetch_source is None and source_filter in (None, "abstract_only"):
            sections = {
                "abstract_full": None,
                "methods_text": None,
                "results_text": None,
                "discussion_text": None,
            }
            fetch_source = "abstract_only"

        if fetch_source is None:
            # source_filter excluded all sources for this article
            continue

        # Determine status
        if sections is None:
            status = "error"
            counters["error"] += 1
            _db_execute_with_retry(conn, """
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, fetch_source, fetch_status)
                VALUES (?, ?, 'error')
            """, (canonical_id, fetch_source))

        elif isinstance(sections, dict) and sections.get("_status") == "not_open_access":
            status = "not_open_access"
            counters["not_oa"] += 1
            _db_execute_with_retry(conn, """
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, fetch_source, fetch_status)
                VALUES (?, ?, 'not_open_access')
            """, (canonical_id, fetch_source))

        else:
            status = "ok"
            if fetch_source == "europe_pmc":
                counters["ok_epmc"] += 1
            elif fetch_source == "semantic_scholar":
                counters["ok_s2"] += 1
            else:
                counters["ok_abstract"] += 1

            _db_execute_with_retry(conn, """
                INSERT OR REPLACE INTO article_fulltexts
                    (canonical_id, fetch_source,
                     abstract_full, methods_text, results_text, discussion_text,
                     fetch_status)
                VALUES (?, ?, ?, ?, ?, ?, 'ok')
            """, (
                canonical_id, fetch_source,
                sections.get("abstract_full"),
                sections.get("methods_text"),
                sections.get("results_text"),
                sections.get("discussion_text"),
            ))

        # Commit every 50 articles so we don't hold the write lock too long
        if i % 50 == 0:
            conn.commit()

    conn.commit()

    total_ok = conn.execute(
        "SELECT COUNT(*) FROM article_fulltexts WHERE fetch_status = 'ok'"
    ).fetchone()[0]
    log.info(
        "Done. europe_pmc=%d | semantic_scholar=%d | abstract_only=%d | "
        "not_oa=%d | error=%d | total ok in DB: %d",
        counters["ok_epmc"], counters["ok_s2"], counters["ok_abstract"],
        counters["not_oa"], counters["error"], total_ok,
    )
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Max articles to fetch (default: all pending)")
    parser.add_argument(
        "--source",
        choices=["europepmc", "semanticscholar", "abstract_only"],
        default=None,
        help="Use only this source (default: cascade through all)"
    )
    args = parser.parse_args()
    run(args.limit, args.source)
