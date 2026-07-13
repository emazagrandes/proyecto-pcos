#!/usr/bin/env python3
"""
Coverage lever: fetch Open Access full text via Unpaywall + PDF parsing.

Why (2026-07): ~4,300/12,155 articles have full text (mostly PMC XML). Of the
~7,500 missing-with-DOI, Unpaywall reports ~41% are Open Access — but almost all
are publisher-hosted PDFs, not section-tagged XML. This module resolves the OA
PDF via the Unpaywall API, downloads it, extracts text with pypdfium2, and
splits it into abstract/methods/results/discussion so the same extractor prompt
(build_source_text) can consume it exactly like PMC/EuropePMC rows.

Pipeline per article (canonical_id with a DOI, no fulltext row yet):
  1. Unpaywall  /v2/{doi}?email=...  -> is_oa + best_oa_location.url_for_pdf
  2. download the PDF (streamed, size-capped)
  3. pypdfium2 -> raw text (all pages)
  4. split_sections() -> abstract/methods/results/discussion (IMRaD heuristic)
  5. write to article_fulltexts with fetch_source='unpaywall_pdf'

Notes / caveats:
  - PDF section splitting is heuristic and noisier than XML. When headers can't be
    found the whole body is stored as abstract_full so nothing is lost (the
    extractor still sees the text; only the section labels are absent).
  - Section caps mirror llm_support / fetch_pmc_fulltext (results 20k etc.).
  - Publisher PDF domains are many and long-tailed; they are NOT on the research
    sandbox allowlist, so bulk download is meant to run on the user's own machine.
    The Unpaywall *resolution* step works anywhere the API is reachable.
  - Idempotent: skips canonical_ids already in article_fulltexts. --dry-run
    resolves + measures without downloading or writing.

Requires: EMAIL for Unpaywall. Pass --email or set UNPAYWALL_EMAIL /
CONTACT_EMAIL env var (Unpaywall requires a contact email on every request).

Usage:
  python scripts/fetch_unpaywall_fulltext.py --limit 10 --dry-run
  python scripts/fetch_unpaywall_fulltext.py --limit 50
  python scripts/fetch_unpaywall_fulltext.py            # all missing-with-DOI
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("unpaywall")

DB_PATH = Path("data/processed/pcos_research.db")
UNPAYWALL_API = "https://api.unpaywall.org/v2/"
REQUEST_DELAY = 0.15           # Unpaywall: 100k/day, be polite
MAX_PDF_BYTES = 30 * 1024 * 1024   # skip anything over 30 MB
SECTION_CAPS = {"abstract_full": 5000, "methods_text": 12000,
                "results_text": 20000, "discussion_text": 10000}

# IMRaD section headers. Order matters: we locate each and slice between them.
# Patterns are matched case-insensitively on a line-start-ish boundary.
_SECTION_PATTERNS = [
    ("abstract_full",   r"\babstract\b"),
    ("_introduction",   r"\b(introduction|background)\b"),
    ("methods_text",    r"\b(materials?\s+and\s+methods?|methods?|patients?\s+and\s+methods?|study\s+design)\b"),
    ("results_text",    r"\bresults?\b"),
    ("discussion_text", r"\b(discussion|limitations)\b"),
    ("_conclusion",     r"\b(conclusions?)\b"),
    ("_references",     r"\b(references?|bibliography|acknowledged?ments?)\b"),
]


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract concatenated text from all pages using pypdfium2."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        parts = []
        for i in range(len(doc)):
            page = doc[i]
            tp = page.get_textpage()
            parts.append(tp.get_text_range())
        return "\n".join(parts)
    finally:
        doc.close()


def split_sections(text: str) -> dict[str, "str | None"]:
    """
    Heuristic IMRaD splitter for PDF-extracted text.

    Finds the first occurrence of each canonical header and slices the text
    between consecutive headers. Robust to missing sections. If no headers are
    found at all, the whole body goes into abstract_full so no text is lost.
    """
    out: dict[str, str | None] = {k: None for k in
                                  ("abstract_full", "methods_text",
                                   "results_text", "discussion_text")}
    if not text or len(text) < 200:
        return out

    low = text.lower()
    # Locate each header's first position.
    hits = []  # (pos, key)
    for key, pat in _SECTION_PATTERNS:
        m = re.search(pat, low)
        if m:
            hits.append((m.start(), key))
    hits.sort()

    if not hits:
        out["abstract_full"] = text[:SECTION_CAPS["abstract_full"]]
        return out

    # Build [start,end) spans between consecutive header hits.
    for idx, (pos, key) in enumerate(hits):
        end = hits[idx + 1][0] if idx + 1 < len(hits) else len(text)
        if key.startswith("_"):      # intro/conclusion/references: not stored
            continue
        seg = text[pos:end].strip()
        cap = SECTION_CAPS.get(key, 5000)
        # Merge if the same key appears twice (rare); keep the longer.
        if out[key] is None or len(seg) > len(out[key]):
            out[key] = seg[:cap]

    # If we found no methods AND no results, fall back to dumping body as abstract
    # so the extractor still gets the content.
    if not out["methods_text"] and not out["results_text"] and not out["abstract_full"]:
        out["abstract_full"] = text[:SECTION_CAPS["abstract_full"]]
    return out


def resolve_oa_pdf(doi: str, email: str) -> "dict | None":
    """Unpaywall lookup -> {'is_oa', 'pdf_url', 'host_type'} or None on error."""
    try:
        r = requests.get(f"{UNPAYWALL_API}{doi}", params={"email": email}, timeout=25)
        if r.status_code != 200:
            return None
        j = r.json()
    except (requests.RequestException, ValueError) as e:
        log.warning("Unpaywall error for %s: %s", doi, e)
        return None
    if not j.get("is_oa"):
        return {"is_oa": False, "pdf_url": None, "host_type": None}
    loc = j.get("best_oa_location") or {}
    pdf_url = loc.get("url_for_pdf")
    # Fallback: scan all locations for any PDF url.
    if not pdf_url:
        for L in (j.get("oa_locations") or []):
            if L.get("url_for_pdf"):
                pdf_url = L["url_for_pdf"]; loc = L; break
    return {"is_oa": True, "pdf_url": pdf_url, "host_type": loc.get("host_type")}


def download_pdf(url: str) -> "bytes | None":
    try:
        r = requests.get(url, timeout=45, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (research fulltext fetcher)"})
        if r.status_code != 200:
            return None
        buf = b""
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > MAX_PDF_BYTES:
                log.warning("PDF over size cap, skipping: %s", url)
                return None
        return buf if buf[:4] == b"%PDF" else None
    except requests.RequestException as e:
        log.warning("PDF download error %s: %s", url, e)
        return None


def run(limit: "int | None", email: str, dry_run: bool) -> None:
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    already = {r[0] for r in conn.execute(
        "SELECT canonical_id FROM article_fulltexts").fetchall()}

    candidates = conn.execute("""
        SELECT canonical_id, doi FROM articles
        WHERE doi IS NOT NULL AND doi != ''
        ORDER BY evidence_score DESC NULLS LAST
    """).fetchall()
    work = [(c, d) for c, d in candidates if c not in already]
    if limit:
        work = work[:limit]
    log.info("Missing-with-DOI to try via Unpaywall: %d (dry_run=%s)", len(work), dry_run)

    n_oa = n_pdf = n_parsed = n_written = n_no_oa = 0
    res_lens = []

    for i, (cid, doi) in enumerate(work):
        if i % 25 == 0 and i > 0 and not dry_run:
            conn.commit()
            log.info("Progress %d/%d | oa=%d pdf=%d parsed=%d written=%d",
                     i, len(work), n_oa, n_pdf, n_parsed, n_written)

        info = resolve_oa_pdf(doi, email)
        time.sleep(REQUEST_DELAY)
        if not info or not info.get("is_oa"):
            n_no_oa += 1
            continue
        n_oa += 1
        pdf_url = info.get("pdf_url")
        if not pdf_url:
            continue

        if dry_run:
            n_pdf += 1
            continue

        pdf_bytes = download_pdf(pdf_url)
        if not pdf_bytes:
            continue
        n_pdf += 1

        try:
            text = extract_pdf_text(pdf_bytes)
        except Exception as e:
            log.warning("PDF parse failed for %s: %s", cid, e)
            continue
        secs = split_sections(text)
        if not any(secs.values()):
            continue
        n_parsed += 1
        res_lens.append(len(secs.get("results_text") or ""))

        conn.execute("""
            INSERT OR REPLACE INTO article_fulltexts
                (canonical_id, pmcid, fetch_source, abstract_full,
                 methods_text, results_text, discussion_text, fetch_status)
            VALUES (?, NULL, 'unpaywall_pdf', ?, ?, ?, ?, 'ok')
        """, (cid, secs.get("abstract_full"), secs.get("methods_text"),
              secs.get("results_text"), secs.get("discussion_text")))
        n_written += 1

    if not dry_run:
        conn.commit()

    avg_res = sum(res_lens) / len(res_lens) if res_lens else 0
    log.info("Done. oa=%d pdf=%d parsed=%d written=%d no_oa=%d | avg results_text=%.0f chars",
             n_oa, n_pdf, n_parsed, n_written, n_no_oa, avg_res)
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--email", type=str,
                    default=os.environ.get("UNPAYWALL_EMAIL")
                            or os.environ.get("CONTACT_EMAIL"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.email:
        sys.exit("Unpaywall requires a contact email: pass --email or set UNPAYWALL_EMAIL")
    run(args.limit, args.email, args.dry_run)
