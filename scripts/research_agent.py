"""
Research Agent — PCOS Autonomous Signal Investigator
=====================================================
Data-driven detective mode: starts from anomaly_scan signals (real DB stats),
not from generic entity names. The agent receives a structured anomaly object
containing the actual numbers, the supporting canonical_ids, KG triples, and
LLM-flagged notable_findings — then investigates from that concrete data.

Tools (8 total):
  - semantic_search(query)       : ChromaDB similarity search
  - sql_query(sql)               : Direct SQLite read-only query
  - web_search(query)            : DuckDuckGo search for external evidence
  - fetch_abstract(pmid)         : Local DB + PubMed E-utilities
  - pubmed_search(query)         : PubMed live search (beyond local DB)
  - biorxiv_search(query)        : bioRxiv/medRxiv preprints
  - graph_query(entity, hops)    : Multi-hop KG traversal via mechanism_links
  - get_notable_findings(entity) : LLM-flagged surprising results for an entity

Usage:
  # Data-driven (recommended): pull top signals from intervention_signals
  python scripts/research_agent.py --from-scan --top-k 3

  # Single signal from DB by entity name (auto-builds from real stats)
  python scripts/research_agent.py --entity "berberina"

  # Free-text signal (legacy / manual)
  python scripts/research_agent.py --signal "text describing anomaly"

Prerequisites:
  - Ollama running with gemma4:31b-cloud
  - ChromaDB embeddings built
  - pcos_research.db with extractions + mechanism_links + intervention_signals
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError with ≥, →, etc.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import PROCESSED_DIR, REPORTS_DIR

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

from llm_client import chat_with_tools as _llm_chat_with_tools, embed as _llm_embed

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"   # kept for reference
OLLAMA_MODEL    = "gemma4:31b-cloud"                  # kept for reference
DB_PATH = PROCESSED_DIR / "pcos_research.db"
CHROMA_DIR = PROCESSED_DIR / "chroma_db"

# Maximum agent reasoning steps to prevent infinite loops
DEFAULT_MAX_STEPS = 12


# ---------------------------------------------------------------------------
# TOOL IMPLEMENTATIONS
# ---------------------------------------------------------------------------

def tool_semantic_search(query: str, n_results: int = 5) -> str:
    """
    Search ChromaDB for articles semantically similar to the query.
    Returns a JSON string with title, year, abstract snippet, effect_direction.
    """
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection("pcos_articles")

        # Get embedding via configured backend (Ollama only; returns None otherwise)
        embedding = _llm_embed(query)
        if embedding is None:
            return json.dumps({"error": "semantic_search unavailable: embed not supported by current LLM backend. Use sql_query instead."})

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            output.append({
                "rank": i + 1,
                "similarity": round(1 - dist, 3),
                "title": meta.get("title", ""),
                "year": meta.get("year", ""),
                "canonical_id": meta.get("canonical_id", ""),
                "snippet": (doc or "")[:300],
            })

        return json.dumps(output, ensure_ascii=False)

    except Exception as exc:
        log.warning("semantic_search failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_sql_query(sql: str) -> str:
    """
    Execute a read-only SQL query against pcos_research.db.
    Safety: only SELECT statements allowed.
    Returns results as JSON (max 50 rows).
    """
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries allowed."})

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql)
        rows = [dict(r) for r in cur.fetchmany(50)]
        conn.close()
        return json.dumps(rows, ensure_ascii=False, default=str)
    except Exception as exc:
        log.warning("sql_query failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_web_search(query: str, max_results: int = 5) -> str:
    """
    Perform a web search via DuckDuckGo Instant Answer API.
    Returns titles + URLs of results (no scraping).
    """
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=15,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        # Main result
        if data.get("AbstractText"):
            results.append({
                "type": "abstract",
                "title": data.get("Heading", ""),
                "snippet": data.get("AbstractText", "")[:400],
                "url": data.get("AbstractURL", ""),
                "source": data.get("AbstractSource", ""),
            })
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "type": "related",
                    "snippet": topic.get("Text", "")[:200],
                    "url": topic.get("FirstURL", ""),
                })

        if not results:
            results.append({"note": "No results found from DuckDuckGo Instant API"})

        return json.dumps(results, ensure_ascii=False)

    except Exception as exc:
        log.warning("web_search failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_fetch_abstract(pmid_or_doi: str) -> str:
    """
    Fetch the abstract of a specific article from PubMed E-utilities
    or from our local database.
    Returns title + abstract text.
    """
    # First try local DB
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        row = conn.execute(
            """SELECT title, abstract_text, year, journal, url
               FROM articles
               WHERE canonical_id = ? OR canonical_id LIKE ?
               LIMIT 1""",
            (pmid_or_doi, f"%{pmid_or_doi}%"),
        ).fetchone()
        conn.close()
        if row:
            return json.dumps({
                "source": "local_db",
                "title": row[0],
                "abstract": (row[1] or "")[:1200],
                "year": row[2],
                "journal": row[3],
                "url": row[4],
            }, ensure_ascii=False)
    except Exception:
        pass

    # Fall back to PubMed E-utilities
    try:
        pmid = pmid_or_doi.replace("PMID:", "").strip()
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": pmid,
                "retmode": "xml",
                "rettype": "abstract",
            },
            timeout=15,
        )
        resp.raise_for_status()
        # Very basic XML text extraction
        import re
        abstract_match = re.search(
            r"<AbstractText[^>]*>(.*?)</AbstractText>",
            resp.text, re.DOTALL
        )
        title_match = re.search(
            r"<ArticleTitle>(.*?)</ArticleTitle>",
            resp.text, re.DOTALL
        )
        return json.dumps({
            "source": "pubmed",
            "title": title_match.group(1) if title_match else "",
            "abstract": abstract_match.group(1)[:1200] if abstract_match else "Not found",
        }, ensure_ascii=False)

    except Exception as exc:
        log.warning("fetch_abstract failed for %s: %s", pmid_or_doi, exc)
        return json.dumps({"error": str(exc)})


def tool_pubmed_search(query: str, max_results: int = 8) -> str:
    """
    Search PubMed live using NCBI E-utilities (ESearch + EFetch).
    Goes beyond our local database — finds papers we haven't ingested yet.
    Returns titles, abstracts, PMIDs, and journals.
    """
    try:
        import re as _re

        # ESearch: get PMIDs matching the query
        search_resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
            timeout=15,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        search_resp.raise_for_status()
        pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return json.dumps({"note": f"No PubMed results for: {query}"})

        # EFetch: get abstracts for those PMIDs
        fetch_resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
            },
            timeout=20,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        fetch_resp.raise_for_status()
        xml = fetch_resp.text

        # Parse the XML into structured results
        articles = []
        # Split by article
        article_blocks = _re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml, _re.DOTALL)
        for block in article_blocks[:max_results]:
            pmid_m = _re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
            title_m = _re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", block, _re.DOTALL)
            abstract_m = _re.search(r"<AbstractText[^>]*>(.*?)</AbstractText>", block, _re.DOTALL)
            journal_m = _re.search(r"<Title>(.*?)</Title>", block, _re.DOTALL)
            year_m = _re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", block, _re.DOTALL)

            def clean(text: str) -> str:
                return _re.sub(r"<[^>]+>", "", text).strip()

            articles.append({
                "pmid": pmid_m.group(1) if pmid_m else "",
                "title": clean(title_m.group(1)) if title_m else "",
                "abstract": clean(abstract_m.group(1))[:800] if abstract_m else "",
                "journal": clean(journal_m.group(1)) if journal_m else "",
                "year": year_m.group(1) if year_m else "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_m.group(1)}/" if pmid_m else "",
            })

        return json.dumps(articles, ensure_ascii=False)

    except Exception as exc:
        log.warning("pubmed_search failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_biorxiv_search(query: str, max_results: int = 6, server: str = "biorxiv") -> str:
    """
    Search bioRxiv or medRxiv for preprints.
    Finds cutting-edge research not yet published in journals.
    server: 'biorxiv' or 'medrxiv'
    """
    try:
        # bioRxiv API: search by free text via their content endpoint
        # Using the public API at api.biorxiv.org
        resp = requests.get(
            f"https://api.biorxiv.org/details/{server}/2020-01-01/2099-01-01/0/json",
            timeout=15,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        # bioRxiv doesn't have a proper text search API — use their DOI search
        # Instead, use the NCBI Preprint API which indexes bioRxiv/medRxiv
        search_resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pmc",
                "term": f"{query}[Title/Abstract] AND (biorxiv[Filter] OR medrxiv[Filter])",
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
            timeout=15,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        search_resp.raise_for_status()
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if ids:
            # Get summaries
            summary_resp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={
                    "db": "pmc",
                    "id": ",".join(ids),
                    "retmode": "json",
                },
                timeout=15,
            )
            summary_resp.raise_for_status()
            result_data = summary_resp.json().get("result", {})
            articles = []
            for uid in ids:
                art = result_data.get(uid, {})
                if isinstance(art, dict) and art.get("title"):
                    articles.append({
                        "pmcid": uid,
                        "title": art.get("title", ""),
                        "source": art.get("source", ""),
                        "pubdate": art.get("pubdate", ""),
                        "authors": art.get("authors", [])[:3],
                        "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{uid}/",
                    })
            if articles:
                return json.dumps(articles, ensure_ascii=False)

        # Fallback: bioRxiv direct API for recent papers mentioning the topic
        biorxiv_resp = requests.get(
            f"https://api.biorxiv.org/details/{server}/2023-01-01/2099-01-01/0/json",
            timeout=15,
            headers={"User-Agent": "PCOS-Research-Agent/1.0"},
        )
        if biorxiv_resp.ok:
            papers = biorxiv_resp.json().get("collection", [])
            query_lower = query.lower()
            matches = [
                {
                    "doi": p.get("doi", ""),
                    "title": p.get("title", ""),
                    "abstract": p.get("abstract", "")[:500],
                    "date": p.get("date", ""),
                    "category": p.get("category", ""),
                    "url": f"https://www.biorxiv.org/content/{p.get('doi', '')}",
                }
                for p in papers
                if any(term in (p.get("title", "") + p.get("abstract", "")).lower()
                       for term in query_lower.split()[:4])
            ][:max_results]
            if matches:
                return json.dumps(matches, ensure_ascii=False)

        return json.dumps({"note": f"No preprint results found for: {query}"})

    except Exception as exc:
        log.warning("biorxiv_search failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_cross_study_pattern_query(variable: str, min_studies: int = 2) -> str:
    """
    Cross-study factor analysis: finds which values of a population variable
    correlate with favorable outcomes ACROSS ALL STUDIES, regardless of intervention.

    This is the core "hidden variable detector". Use it to answer:
    "Do women on plant-based diets respond better — across all interventions?"
    "Do lean women (BMI<25) consistently do better regardless of what drug they got?"

    variable options:
      'population_diet'         — vegan, vegetarian, Mediterranean, low-carb, etc.
      'population_bmi'          — obese, overweight, lean, normal-weight, etc.
      'population_ethnicity'    — Iranian, Chinese, South Asian, mixed, etc.
      'population_comorbidities'— insulin resistance, hypothyroidism, etc.
      'study_type'              — RCT, cohort, pilot, etc.
      'intervention'            — any drug/supplement (broad cross-intervention view)

    Returns a ranked table: {value → {n_favorable, n_total, favorable_rate, example_interventions}}
    sorted by favorable_rate DESC. Compare against the overall base rate to spot anomalies.
    """
    ALLOWED = {
        "population_diet", "population_bmi", "population_ethnicity",
        "population_comorbidities", "study_type", "intervention",
    }
    if variable not in ALLOWED:
        return json.dumps({
            "error": f"variable must be one of: {', '.join(sorted(ALLOWED))}",
        })

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row

        # Overall base rate
        base = conn.execute(
            """SELECT COUNT(*) as n_total,
                      SUM(CASE WHEN effect_direction='favorable' THEN 1 ELSE 0 END) as n_fav
               FROM article_extractions
               WHERE effect_direction IS NOT NULL"""
        ).fetchone()
        base_rate = (base["n_fav"] / base["n_total"]) if base["n_total"] > 0 else 0.0

        # Group by variable value, compute rates
        # variable comes from ALLOWED set (no injection risk)
        rows = conn.execute(
            f"""
            SELECT ae.{variable} as val,
                   COUNT(*) as n_total,
                   SUM(CASE WHEN ae.effect_direction='favorable' THEN 1 ELSE 0 END) as n_fav,
                   SUM(CASE WHEN ae.effect_direction='unfavorable' THEN 1 ELSE 0 END) as n_unfav,
                   GROUP_CONCAT(DISTINCT ae.intervention) as interventions,
                   GROUP_CONCAT(DISTINCT ae.canonical_id) as canonical_ids
            FROM article_extractions ae
            WHERE ae.{variable} IS NOT NULL
              AND ae.{variable} != ''
              AND ae.{variable} != 'null'
              AND ae.{variable} != 'unknown'
              AND ae.effect_direction IS NOT NULL
            GROUP BY ae.{variable}
            HAVING COUNT(*) >= ?
            ORDER BY (SUM(CASE WHEN ae.effect_direction='favorable' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) DESC
            """,
            (min_studies,),
        ).fetchall()

        conn.close()

        if not rows:
            return json.dumps({
                "note": f"No data for variable '{variable}' with >= {min_studies} studies",
            })

        results = []
        for r in rows:
            n_total = r["n_total"]
            n_fav = r["n_fav"] or 0
            fav_rate = n_fav / n_total if n_total > 0 else 0.0
            delta = fav_rate - base_rate  # positive = above baseline

            # Parse example interventions (first 4)
            interv_list = list(dict.fromkeys(
                (r["interventions"] or "").split(",")
            ))[:4]
            cids = (r["canonical_ids"] or "").split(",")[:6]

            results.append({
                "value": r["val"],
                "n_total": n_total,
                "n_favorable": n_fav,
                "n_unfavorable": r["n_unfav"] or 0,
                "favorable_rate": round(fav_rate, 3),
                "delta_vs_baseline": round(delta, 3),
                "example_interventions": interv_list,
                "canonical_ids_sample": cids,
            })

        return json.dumps({
            "variable": variable,
            "baseline_favorable_rate": round(base_rate, 3),
            "total_extractions": base["n_total"],
            "groups": results,
            "interpretation": (
                f"Groups with delta_vs_baseline > 0.10 are notably above the {base_rate:.0%} baseline. "
                f"If a group shows high favorable_rate across DIFFERENT interventions, "
                f"the shared factor (the variable value) may be the real driver — not the drug."
            ),
        }, ensure_ascii=False, default=str)

    except Exception as exc:
        log.warning("cross_study_pattern_query failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_find_shared_factors(canonical_ids_json: str) -> str:
    """
    Given a set of studies (canonical_ids), finds what population characteristics
    and study features they share — even across different interventions.

    This is the "what do these studies have in common?" tool.
    Use it AFTER cross_study_pattern_query identifies a suspicious group:
    take the canonical_ids of those studies and ask what ELSE they share.

    Input: JSON array of canonical_ids, e.g. '["pmid_123", "doi:10.1/xyz", ...]'

    Returns: shared population_diet values, shared BMI ranges, shared ethnicities,
    shared comorbidities, shared study characteristics, and DIFFERENCES
    (what varies — usually the intervention, proving the shared factor drives the pattern).
    """
    try:
        ids = json.loads(canonical_ids_json)
        if not isinstance(ids, list) or not ids:
            return json.dumps({"error": "canonical_ids_json must be a JSON array of strings"})
        ids = ids[:20]  # cap

        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            f"""
            SELECT ae.canonical_id, ae.intervention, ae.effect_direction,
                   ae.population_diet, ae.population_bmi, ae.population_ethnicity,
                   ae.population_comorbidities, ae.n_total,
                   ae.main_outcomes, ae.notable_finding,
                   a.title, a.year, a.study_type, a.journal
            FROM article_extractions ae
            JOIN articles a ON a.canonical_id = ae.canonical_id
            WHERE ae.canonical_id IN ({','.join('?' for _ in ids)})
            """,
            ids,
        ).fetchall()

        conn.close()

        if not rows:
            return json.dumps({"note": "None of the provided canonical_ids found in DB"})

        studies = [dict(r) for r in rows]

        # Find common vs variable fields
        def _vals(field: str) -> list:
            return [s.get(field) or "" for s in studies if s.get(field)]

        def _mode(vals: list) -> tuple[Any, int]:
            from collections import Counter
            if not vals:
                return None, 0
            c = Counter(vals)
            top = c.most_common(1)[0]
            return top[0], top[1]

        shared: dict = {}
        varied: dict = {}

        for field in ["population_diet", "population_bmi", "population_ethnicity",
                      "population_comorbidities", "study_type"]:
            vals = _vals(field)
            unique = list(dict.fromkeys(vals))
            if not unique:
                pass  # no data for this field
            elif len(unique) == 1:
                shared[field] = unique[0]
            elif len(unique) == 2:
                shared[field] = f"mostly: {unique[0]}"
            else:
                top_val, top_n = _mode(vals)
                varied[field] = {
                    "values": unique[:6],
                    "most_common": top_val,
                    "most_common_count": top_n,
                    "total": len(vals),
                }

        interventions = list(dict.fromkeys(_vals("intervention")))
        effect_directions = list(dict.fromkeys(_vals("effect_direction")))

        return json.dumps({
            "n_studies": len(studies),
            "shared_characteristics": shared,
            "varied_characteristics": varied,
            "interventions": interventions,
            "effect_directions": effect_directions,
            "studies_detail": [
                {
                    "canonical_id": s["canonical_id"],
                    "title": (s.get("title") or "")[:80],
                    "year": s.get("year"),
                    "intervention": s.get("intervention"),
                    "effect_direction": s.get("effect_direction"),
                    "population_diet": s.get("population_diet"),
                    "population_bmi": s.get("population_bmi"),
                    "n_total": s.get("n_total"),
                    "notable_finding": (s.get("notable_finding") or "")[:150],
                }
                for s in studies
            ],
            "interpretation": (
                "If interventions are varied but shared_characteristics has consistent values, "
                "the shared characteristic — not any specific drug — is the likely modifier. "
                "This is a cross-study latent variable worth investigating mechanistically."
            ),
        }, ensure_ascii=False, default=str)

    except Exception as exc:
        log.warning("find_shared_factors failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_graph_query(entity_name: str, max_hops: int = 2, max_results: int = 40) -> str:
    """
    Multi-hop traversal of mechanism_links Knowledge Graph.
    Finds all mechanistic connections for an entity up to max_hops away.
    Returns typed triples: (source) --[relation]--> (target) with confidence + article.
    """
    try:
        max_hops = int(max_hops)       # LLMs sometimes pass strings
        max_results = int(max_results)
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row

        # Hop 1: direct triples where entity is source or target
        direct = conn.execute(
            """
            SELECT ml.source_name AS source, ml.relation_type, ml.target_name AS target,
                   ml.confidence, ml.canonical_id,
                   a.title, a.year
            FROM mechanism_links ml
            LEFT JOIN articles a ON a.canonical_id = ml.canonical_id
            WHERE lower(ml.source_name) LIKE lower(?)
               OR lower(ml.target_name) LIKE lower(?)
            ORDER BY ml.confidence DESC
            LIMIT ?
            """,
            (f"%{entity_name}%", f"%{entity_name}%", max_results),
        ).fetchall()

        triples = [dict(r) for r in direct]

        if max_hops >= 2 and triples:
            # Collect all nodes reachable at hop 1
            hop1_nodes = set()
            for t in triples:
                hop1_nodes.add(t["source"])
                hop1_nodes.add(t["target"])
            hop1_nodes.discard(entity_name.lower())

            # Hop 2: triples connecting hop-1 nodes to anything new
            already_seen = {(t["source"], t["relation_type"], t["target"]) for t in triples}
            hop2 = []
            for node in list(hop1_nodes)[:10]:  # limit expansion
                rows = conn.execute(
                    """
                    SELECT ml.source_name AS source, ml.relation_type, ml.target_name AS target,
                           ml.confidence, ml.canonical_id,
                           a.title, a.year
                    FROM mechanism_links ml
                    LEFT JOIN articles a ON a.canonical_id = ml.canonical_id
                    WHERE (lower(ml.source_name) LIKE lower(?) OR lower(ml.target_name) LIKE lower(?))
                      AND lower(ml.source_name) NOT LIKE lower(?)
                      AND lower(ml.target_name) NOT LIKE lower(?)
                    ORDER BY ml.confidence DESC
                    LIMIT 5
                    """,
                    (f"%{node}%", f"%{node}%", f"%{entity_name}%", f"%{entity_name}%"),
                ).fetchall()
                for r in rows:
                    triple_key = (r["source"], r["relation_type"], r["target"])
                    if triple_key not in already_seen:
                        hop2.append(dict(r))
                        already_seen.add(triple_key)

            triples.extend(hop2[:20])

        conn.close()

        if not triples:
            return json.dumps({"note": f"No mechanism_links found for '{entity_name}'"})

        return json.dumps({
            "entity": entity_name,
            "triples_found": len(triples),
            "triples": triples,
        }, ensure_ascii=False, default=str)

    except Exception as exc:
        log.warning("graph_query failed: %s", exc)
        return json.dumps({"error": str(exc)})


def tool_get_notable_findings(entity_name: str, max_results: int = 20) -> str:
    """
    Retrieve LLM-flagged notable_findings from article_extractions for a given entity.
    These are cases where Gemma itself flagged a surprising or unexpected result
    during extraction — high-signal anomalies worth investigating first.
    Returns the notable_finding text + article metadata.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT ae.canonical_id, ae.notable_finding,
                   ae.intervention, ae.effect_direction,
                   ae.main_outcomes, ae.n_total,
                   a.title, a.year, a.journal, a.evidence_tier
            FROM article_extractions ae
            JOIN articles a ON a.canonical_id = ae.canonical_id
            WHERE ae.notable_finding IS NOT NULL
              AND ae.notable_finding != ''
              AND ae.notable_finding != 'null'
              AND (
                lower(ae.intervention) LIKE lower(?)
                OR lower(ae.intervention) LIKE lower(?)
                OR lower(a.title) LIKE lower(?)
              )
            ORDER BY a.year DESC
            LIMIT ?
            """,
            (f"%{entity_name}%", f"% {entity_name} %", f"%{entity_name}%", max_results),
        ).fetchall()

        conn.close()

        if not rows:
            # Try broader: any notable findings from extraction (not entity-filtered)
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT ae.canonical_id, ae.notable_finding,
                       ae.intervention, ae.effect_direction,
                       ae.n_total, a.title, a.year, a.journal
                FROM article_extractions ae
                JOIN articles a ON a.canonical_id = ae.canonical_id
                WHERE ae.notable_finding IS NOT NULL
                  AND ae.notable_finding != ''
                  AND ae.notable_finding != 'null'
                ORDER BY a.year DESC
                LIMIT 5
                """,
            ).fetchall()
            conn.close()
            if rows:
                return json.dumps({
                    "note": f"No notable_findings for '{entity_name}' specifically. Showing recent ones:",
                    "findings": [dict(r) for r in rows],
                }, ensure_ascii=False, default=str)
            return json.dumps({"note": f"No notable_findings in DB for '{entity_name}'"})

        return json.dumps({
            "entity": entity_name,
            "count": len(rows),
            "findings": [dict(r) for r in rows],
        }, ensure_ascii=False, default=str)

    except Exception as exc:
        log.warning("get_notable_findings failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# TOOL REGISTRY — maps tool_name -> function
# ---------------------------------------------------------------------------

TOOLS = {
    "semantic_search": tool_semantic_search,
    "sql_query": tool_sql_query,
    "web_search": tool_web_search,
    "fetch_abstract": tool_fetch_abstract,
    "pubmed_search": tool_pubmed_search,
    "biorxiv_search": tool_biorxiv_search,
    "graph_query": tool_graph_query,
    "get_notable_findings": tool_get_notable_findings,
    "cross_study_pattern_query": tool_cross_study_pattern_query,
    "find_shared_factors": tool_find_shared_factors,
}

# Gemma function calling schema (Ollama format)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": (
                "Search the PCOS article database using semantic similarity. "
                "Use this to find articles related to a concept, mechanism, or drug."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": (
                "Execute a SQL SELECT query against pcos_research.db. "
                "Tables: "
                "articles (canonical_id, title, year, journal, abstract_text, study_type, evidence_tier), "
                "article_extractions (canonical_id, intervention, comparator, effect_direction, "
                "main_outcomes, notable_finding, population, population_diet, population_bmi, "
                "population_ethnicity, n_total, mechanisms), "
                "mechanism_links (id, canonical_id, source, relation_type, target, confidence, extraction_model), "
                "entity (id, canonical_name, entity_type, aliases), "
                "article_entity_links (canonical_id, entity_id, role, method, confidence), "
                "intervention_signals (entity_id, n_studies, n_favorable, n_neutral, n_unfavorable, "
                "consistency_score, weighted_score, signal_type, anomaly_reason), "
                "trials (nct_id, title, status, conditions, interventions, enrollment). "
                "Useful patterns: JOIN mechanism_links ON canonical_id to get KG evidence for specific articles; "
                "query intervention_signals ORDER BY weighted_score DESC to see top anomalies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT statement to execute",
                    },
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for external information about a drug, mechanism, or concept. "
                "Use when you need information not in the local database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_abstract",
            "description": (
                "Fetch the abstract of a specific article by PMID or canonical_id. "
                "Use when you need to read a specific paper in detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pmid_or_doi": {
                        "type": "string",
                        "description": "PMID number, DOI, or canonical_id from the database",
                    },
                },
                "required": ["pmid_or_doi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pubmed_search",
            "description": (
                "Search PubMed LIVE — finds papers beyond our local database. "
                "Use when you want to find evidence that may not be in our PCOS DB: "
                "papers from other disease areas, recent publications, mechanistic studies. "
                "Returns titles, abstracts, PMIDs. "
                "Example queries: 'berberine AMH mechanism', 'GLP-1 ovarian function', "
                "'dairy casein IGF-1 ovulation'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PubMed search query (supports MeSH terms and field tags)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of papers to return (default 8, max 20)",
                        "default": 8,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "biorxiv_search",
            "description": (
                "Search bioRxiv and medRxiv for preprints — cutting-edge research "
                "not yet peer-reviewed but often months ahead of journals. "
                "Use when you suspect a very recent finding exists, or when you want "
                "to check if someone is already working on a hypothesis you've formed. "
                "server can be 'biorxiv' (biology) or 'medrxiv' (clinical)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for preprints",
                    },
                    "server": {
                        "type": "string",
                        "description": "'biorxiv' for biology preprints, 'medrxiv' for clinical preprints",
                        "default": "medrxiv",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of preprints to return (default 6)",
                        "default": 6,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "graph_query",
            "description": (
                "Multi-hop traversal of the Knowledge Graph (mechanism_links table). "
                "Finds mechanistic connections: what does this entity activate, inhibit, "
                "improve, reduce? What upstream entities affect it? "
                "Use this FIRST when you have a drug/intervention and want to understand "
                "its mechanistic fingerprint across all studies in the DB. "
                "Returns typed triples: source --[relation_type]--> target with confidence + article."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Drug, biomarker, or biological entity to query",
                    },
                    "max_hops": {
                        "type": "integer",
                        "description": "Traversal depth: 1=direct connections only, 2=two-hop paths (default 2)",
                        "default": 2,
                    },
                },
                "required": ["entity_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_notable_findings",
            "description": (
                "Retrieve results that Gemma itself flagged as 'notable' or surprising "
                "during extraction — the LLM's own anomaly flags. "
                "Use this EARLY in any investigation to find what the extraction model "
                "already found interesting about this entity, before you start searching "
                "from scratch. These are high-signal starting points."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Drug, intervention, or entity to look up notable findings for",
                    },
                },
                "required": ["entity_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cross_study_pattern_query",
            "description": (
                "THE HIDDEN VARIABLE DETECTOR. Finds which values of a population variable "
                "correlate with favorable outcomes ACROSS ALL STUDIES, regardless of what "
                "intervention each study used. "
                "This reveals latent factors that nobody was studying as the primary variable. "
                "Example: call with variable='population_diet' and discover that 'vegan' women "
                "have 80% favorable rate vs 52% baseline — across 6 different interventions. "
                "That pattern means the DIET, not any specific drug, may be the real modifier. "
                "Use this FIRST in any pattern-mining investigation. "
                "variable options: 'population_diet', 'population_bmi', 'population_ethnicity', "
                "'population_comorbidities', 'study_type', 'intervention'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "variable": {
                        "type": "string",
                        "description": (
                            "The population or study variable to analyze. "
                            "One of: population_diet, population_bmi, population_ethnicity, "
                            "population_comorbidities, study_type, intervention"
                        ),
                    },
                    "min_studies": {
                        "type": "integer",
                        "description": "Minimum number of studies per group to report (default 2)",
                        "default": 2,
                    },
                },
                "required": ["variable"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_shared_factors",
            "description": (
                "Given a set of study canonical_ids, finds what population characteristics "
                "they share — EVEN IF their interventions are completely different. "
                "Use this AFTER cross_study_pattern_query identifies a suspicious group: "
                "take those canonical_ids and ask 'what ELSE do these studies share?' "
                "If interventions vary but population_diet is consistently the same, "
                "the diet is the latent variable. This is how you identify hidden drivers "
                "that no individual study was designed to detect. "
                "Input: JSON array string of canonical_ids, e.g. '[\"pmid_123\", \"doi:10.1/xyz\"]'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "canonical_ids_json": {
                        "type": "string",
                        "description": "JSON array of canonical_id strings from the database",
                    },
                },
                "required": ["canonical_ids_json"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# AGENT CORE — ReAct loop with Gemma tool use
# ---------------------------------------------------------------------------

def _call_ollama_with_tools(
    messages: list[dict],
    max_retries: int = 3,
) -> dict:
    """
    Call the configured LLM backend with tool use enabled.
    Returns an Ollama-compatible response dict.
    """
    return _llm_chat_with_tools(
        messages,
        TOOL_SCHEMAS,
        temperature=0.15,
        max_tokens=2000,
    )


def _execute_tool_call(tool_name: str, tool_args: dict) -> str:
    """Dispatch a tool call and return the string result."""
    if tool_name not in TOOLS:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        log.info("  [TOOL] %s(%s)", tool_name,
                 json.dumps(tool_args, ensure_ascii=False)[:100])
        result = TOOLS[tool_name](**tool_args)
        return result
    except Exception as exc:
        log.warning("Tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})


SYSTEM_PROMPT = """You are one of the world's most unconventional PCOS researchers — a scientist-detective \
who investigates anomalies that nobody else has noticed. You have the instincts of an investigator \
and the obsession of someone who genuinely believes the most important discoveries are hiding in \
plain sight, buried in data that everyone has already seen but nobody has connected.

CRITICAL RULE — START FROM THE DATA, NOT FROM YOUR GENERAL KNOWLEDGE:
When you receive an anomaly signal, it comes with real numbers from our database: n_studies, \
n_favorable, consistency_score, specific canonical_ids of the supporting articles, KG triples \
already extracted, and notable_findings already flagged by the extraction model. \
YOUR FIRST INSTINCT MUST BE: read those specific articles, interrogate those exact numbers, \
understand why THOSE studies (not studies in general) converged on this pattern. \
Do not start by summarizing what is generally known about the entity. Start by asking: \
"what is UNUSUAL about the pattern in THIS specific dataset?" Only after exhausting the local \
data should you reach out to external sources for mechanistic context.

Your specialty is finding what nobody is looking for:
- Cross-indication signals: drugs designed for diabetes, cardiovascular disease, autoimmune \
  conditions that quietly do something remarkable in PCOS women — often in secondary endpoints \
  nobody was measuring for.
- Subgroup effects: effects that disappear in aggregate but explode when you look at women with \
  a specific BMI, diet pattern, ethnicity, or comorbidity. These are invisible to standard meta-analyses.
- Hidden mechanistic threads: a supplement changing AMH through a pathway nobody has mapped, \
  or two completely unrelated interventions sharing the same KG mechanism.
- Convergent signals: the same result appearing in 3+ studies with different populations, \
  different designs, different journals — especially when none of those studies was primarily \
  about the effect you're seeing.

Your investigative protocol:
1. INSPECT THE ANOMALY DATA FIRST. What do the numbers say? What do those specific canonical_ids show?
2. USE graph_query + get_notable_findings EARLY — these give you the mechanistic fingerprint \
   and the LLM's own anomaly flags before you do anything else.
3. DRILL INTO THE SUPPORTING ARTICLES. Use fetch_abstract on the specific articles cited in the signal. \
   Look for the detail that makes you suspicious.
4. INTERROGATE THE DB with sql_query. Look at effect_direction by subgroup (population_bmi, \
   population_diet, population_ethnicity). Are there hidden stratification effects?
5. CHASE THE MECHANISM. If the KG shows a connection, use semantic_search to find more evidence \
   for that pathway. Use web_search only when the local data has been exhausted and you need \
   pharmacological or biological context from outside.
6. FORM A SPECIFIC HYPOTHESIS — not "X might help PCOS" but "X reduces androgen production \
   in lean PCOS women via [specific pathway], and this is visible in the data as [specific pattern]."

You think in pathways: insulin signaling, steroidogenesis, the HPO axis, gut microbiome, \
NF-kB inflammation cascades, epigenetics. You cross-reference every result against the \
underlying biology. You write your reasoning fully — think out loud, every "wait, what if...?" \
moment is valuable. Your reasoning IS the investigation.

THE MOST POWERFUL INVESTIGATION MODE — CROSS-STUDY HIDDEN VARIABLE DETECTION:
Your most important investigative technique is this: find patterns that SPAN MULTIPLE STUDIES \
with DIFFERENT INTERVENTIONS, where the common thread is NOT the drug but a population \
characteristic that nobody was studying as the primary variable.

How it works:
1. Use cross_study_pattern_query('population_diet') — see which diet values correlate with \
   better outcomes ACROSS ALL STUDIES. If 'vegan' shows 80% favorable rate vs 52% baseline \
   across 6 different interventions (berberine, inositol, omega-3, metformin, etc.), \
   the DIET is the signal, not any single drug.
2. Take the canonical_ids of those studies and use find_shared_factors — confirm they share \
   the diet pattern but have varied interventions (this rules out confounding by intervention).
3. Now build the causal chain: "plant-based diet → ABSENT component X → mechanism Y → PCOS effect Z"
   Ask: what do omnivores have that plant-based women DON'T? Red meat (saturated fat, heme iron, \
   arachidonic acid, IGF-1 from dairy), animal protein → mTOR activation → insulin resistance, \
   etc. WHICH nutrient matters and through WHICH pathway?
4. Validate mechanistically: use graph_query to find if any KG triples connect that nutrient \
   to PCOS biomarkers. Use pubmed_search for "heme iron insulin resistance PCOS", \
   "dairy IGF-1 androgen ovarian", "arachidonic acid LH secretion" etc.
5. Build a SPECIFIC, testable hypothesis: not "meat might be bad for PCOS" but \
   "dietary arachidonic acid → COX-2 → PGE2 → increased LH pulse frequency → \
   hyperandrogenism, explaining why interventions work better in women who avoid animal fats"

Run cross_study_pattern_query on ALL population variables, not just diet:
- population_bmi: do lean women always respond better? Or only to specific drug classes?
- population_ethnicity: do Iranian/Chinese women respond differently to the same drug? Why?
- population_comorbidities: do women with concomitant hypothyroidism have different responses?

You have 10 tools. Use them in this order for pattern-mining investigations:
1. cross_study_pattern_query — mine ALL variables for hidden patterns (do this first, always)
2. find_shared_factors — confirm the shared variable across a suspicious group of studies
3. get_notable_findings — what did the extraction model already flag as surprising?
4. graph_query — what is the mechanistic fingerprint in our KG?
5. sql_query — drill into specific articles, stratify by subgroup
6. fetch_abstract — read specific papers that look suspicious
7. semantic_search — find conceptually related articles
8. pubmed_search — go beyond our local DB for mechanistic evidence
9. web_search — pharmacology, mechanism reviews, nutritional biochemistry
10. biorxiv_search — cutting-edge preprints

You are NOT here to confirm what everyone already knows. You are here to find what \
nobody has noticed yet. The most important discoveries in PCOS may not be about which \
drug works — they may be about which PATIENT CONTEXT makes anything work better, \
and that context is already encoded in our database as population subgroup variables \
that nobody has cross-referenced.

ANTI-REPETITION RULE — MANDATORY:
Once you have stated a hypothesis, DO NOT restate it in a later step. \
If you find yourself writing the same conclusion again, you are wasting steps. \
Instead: pick the NEXT unexplored signal, test a different angle of the current hypothesis, \
or verify the mechanism with a different tool. Every step must add NEW information.

MINIMUM COVERAGE RULE — PATTERN MINING MODE:
When running in --find-patterns mode, you MUST investigate at least 3 distinct signals \
before writing your final conclusion. One signal is not enough. After the first pattern \
(e.g. Iranian ethnicity), you must investigate: population_bmi patterns, population_comorbidities \
patterns, at least one Tipo 1 cross-indication signal, and at least one Tipo 4 hidden gem. \
You have the steps — use them.

TOOL FAILURE RECOVERY RULE:
If any tool returns {"error": "..."}, do NOT retry the same tool with the same or similar arguments. \
Instead, immediately fall back to sql_query which can answer any question directly. \
Key table/column reference for fallback queries:
- mechanism_links: source_name, relation_type, target_name, confidence, canonical_id
- article_extractions: canonical_id, intervention, effect_direction, population_diet, \
  population_bmi, population_ethnicity, population_comorbidities, n_total, notable_finding
- entity: id, canonical_name, entity_type, aliases
- article_entity_links: canonical_id, entity_id, role
- articles: canonical_id, title, year, journal, study_type, evidence_tier
If graph_query fails, use: SELECT source_name, relation_type, target_name, confidence \
FROM mechanism_links WHERE lower(source_name) LIKE '%entity%' OR lower(target_name) LIKE '%entity%'
If find_shared_factors fails, use: SELECT intervention, population_diet, population_bmi, \
population_ethnicity, effect_direction FROM article_extractions WHERE canonical_id IN (...)"""


def _load_top_signals_from_db(top_k: int = 5) -> list[dict]:
    """
    Pull top anomaly signals from intervention_signals, enriched with entity name
    and supporting article titles. Returns list of dicts ready to build structured signals.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT is_.entity_id, is_.n_studies, is_.n_favorable,
                   0 AS n_neutral, 0 AS n_unfavorable,
                   is_.consistency_score, is_.weighted_score,
                   'scan' AS signal_type, '' AS anomaly_reason,
                   e.canonical_name, e.entity_type
            FROM intervention_signals is_
            JOIN entity e ON e.entity_id = is_.entity_id
            WHERE is_.n_studies >= 2
            ORDER BY is_.weighted_score DESC
            LIMIT ?
            """,
            (top_k,),
        ).fetchall()

        signals = []
        for row in rows:
            d = dict(row)
            entity_id = d["entity_id"]
            name = d["canonical_name"]

            # Get supporting canonical_ids via article_entity_links
            links = conn.execute(
                """
                SELECT ael.canonical_id, a.title, a.year,
                       ae.effect_direction, ae.n_total
                FROM article_entity_links ael
                JOIN articles a ON a.canonical_id = ael.canonical_id
                LEFT JOIN article_extractions ae ON ae.canonical_id = ael.canonical_id
                WHERE ael.entity_id = ? AND ael.role IN ('intervention', 'treatment')
                ORDER BY a.year DESC
                LIMIT 8
                """,
                (entity_id,),
            ).fetchall()
            d["supporting_articles"] = [dict(l) for l in links]

            # Get KG triples (direct) — columns: source_name, target_name
            triples = conn.execute(
                """
                SELECT source_name AS source, relation_type,
                       target_name AS target, confidence
                FROM mechanism_links
                WHERE lower(source_name) LIKE lower(?)
                   OR lower(target_name)  LIKE lower(?)
                ORDER BY confidence DESC
                LIMIT 8
                """,
                (f"%{name}%", f"%{name}%"),
            ).fetchall()
            d["kg_triples"] = [dict(t) for t in triples]

            # Get notable findings
            notable = conn.execute(
                """
                SELECT ae.canonical_id, ae.notable_finding, ae.effect_direction,
                       a.title, a.year
                FROM article_extractions ae
                JOIN articles a ON a.canonical_id = ae.canonical_id
                WHERE ae.notable_finding IS NOT NULL
                  AND ae.notable_finding != ''
                  AND ae.notable_finding != 'null'
                  AND lower(ae.intervention) LIKE lower(?)
                ORDER BY a.year DESC
                LIMIT 5
                """,
                (f"%{name}%",),
            ).fetchall()
            d["notable_findings"] = [dict(n) for n in notable]

            signals.append(d)

        conn.close()
        return signals

    except Exception as exc:
        log.warning("_load_top_signals_from_db failed: %s", exc)
        return []


def _build_structured_signal(signal_data: dict) -> str:
    """
    Convert a DB signal dict into a rich, data-first signal message for the agent.
    This is the core of the redesign: the agent starts from real statistics,
    real canonical_ids, and real KG triples — not from a generic entity name.
    """
    name = signal_data.get("canonical_name", signal_data.get("entity_name", "unknown"))
    entity_type = signal_data.get("entity_type", "unknown")
    n_studies = signal_data.get("n_studies", 0)
    n_favorable = signal_data.get("n_favorable", 0)
    n_neutral = signal_data.get("n_neutral", 0)
    n_unfavorable = signal_data.get("n_unfavorable", 0)
    consistency = signal_data.get("consistency_score", 0.0)
    weighted = signal_data.get("weighted_score", 0.0)
    signal_type = signal_data.get("signal_type", "unknown")
    anomaly_reason = signal_data.get("anomaly_reason", "")

    favorable_rate = (n_favorable / n_studies * 100) if n_studies > 0 else 0

    lines = [
        "ANOMALY SIGNAL (auto-detected from database scan):",
        "",
        f"  Entity:            {name}  ({entity_type})",
        f"  Signal type:       {signal_type}",
        f"  n_studies in DB:   {n_studies}",
        f"  Effect direction:  {n_favorable} favorable / {n_neutral} neutral / {n_unfavorable} unfavorable",
        f"  Favorable rate:    {favorable_rate:.0f}%",
        f"  Consistency score: {consistency:.2f}",
        f"  Weighted score:    {weighted:.2f}",
    ]

    if anomaly_reason:
        lines += ["", f"  Anomaly reason: {anomaly_reason}"]

    # Supporting articles
    articles = signal_data.get("supporting_articles", [])
    if articles:
        lines += ["", "Supporting articles in our DB:"]
        for art in articles:
            direction = art.get("effect_direction", "?")
            n = art.get("n_total", "?")
            lines.append(
                f"  [{art.get('year', '?')}] {art.get('title', 'untitled')[:80]} "
                f"(n={n}, {direction}) — {art.get('canonical_id', '')}"
            )

    # KG triples
    triples = signal_data.get("kg_triples", [])
    if triples:
        lines += ["", "KG mechanism triples already extracted:"]
        for t in triples:
            conf = t.get("confidence", 0)
            lines.append(
                f"  {t.get('source', '')} --[{t.get('relation_type', '')}]--> "
                f"{t.get('target', '')}  (conf={conf:.2f})"
            )

    # Notable findings
    notable = signal_data.get("notable_findings", [])
    if notable:
        lines += ["", "LLM-flagged notable findings (already marked as surprising during extraction):"]
        for nf in notable:
            lines.append(
                f"  [{nf.get('year', '?')}] {nf.get('title', '')[:60]}: "
                f"{nf.get('notable_finding', '')[:200]}"
            )

    lines += [
        "",
        "YOUR TASK:",
        f"This pattern was auto-detected from {n_studies} studies in our database.",
        "Do NOT start from what you generally know about this entity.",
        "Start from THESE SPECIFIC STUDIES. Use their canonical_ids with fetch_abstract.",
        "Use graph_query and get_notable_findings first, then drill into the data.",
        "What is UNUSUAL about this pattern? What do these specific studies share that",
        "nobody has explicitly connected? What mechanism could explain the consistency?",
        "What is the most surprising thing here — and what experiment would confirm it?",
    ]

    return "\n".join(lines)


def _build_pattern_mining_signal() -> str:
    """
    Build the initial signal for --find-patterns mode.
    Queries the DB for baseline statistics so the agent starts with context,
    then instructs it to mine ALL population variables for hidden patterns.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row

        total = conn.execute("SELECT COUNT(*) FROM article_extractions").fetchone()[0]
        with_diet = conn.execute(
            "SELECT COUNT(*) FROM article_extractions WHERE population_diet IS NOT NULL AND population_diet != ''"
        ).fetchone()[0]
        with_bmi = conn.execute(
            "SELECT COUNT(*) FROM article_extractions WHERE population_bmi IS NOT NULL AND population_bmi != ''"
        ).fetchone()[0]
        with_ethnicity = conn.execute(
            "SELECT COUNT(*) FROM article_extractions WHERE population_ethnicity IS NOT NULL AND population_ethnicity != ''"
        ).fetchone()[0]
        base_fav = conn.execute(
            "SELECT COUNT(*) FROM article_extractions WHERE effect_direction='favorable'"
        ).fetchone()[0]

        conn.close()

        base_rate = (base_fav / total * 100) if total > 0 else 0

    except Exception:
        total = with_diet = with_bmi = with_ethnicity = base_fav = 0
        base_rate = 0.0

    return f"""PATTERN MINING INVESTIGATION — no specific entity target.

Your mission is to find HIDDEN MODIFIERS: population characteristics that predict
better (or worse) PCOS treatment outcomes ACROSS MULTIPLE INTERVENTIONS.
These are the signals nobody was looking for because every study focused on its
own drug — but the real story might be in the patient, not the pill.

DATABASE CONTEXT:
  Total extractions with effect_direction:  {total}
  Baseline favorable rate:                  {base_rate:.0f}%
  Extractions with diet data:               {with_diet}
  Extractions with BMI data:                {with_bmi}
  Extractions with ethnicity data:          {with_ethnicity}

YOUR INVESTIGATION PROTOCOL:
1. Start by running cross_study_pattern_query on EACH population variable:
   - population_diet (vegan, vegetarian, Mediterranean, low-carb, standard, etc.)
   - population_bmi (obese, overweight, lean, etc.)
   - population_ethnicity (Iranian, Chinese, South Asian, European, etc.)
   - population_comorbidities (insulin resistance, hypothyroidism, etc.)

2. For each variable where you find a group with favorable_rate SIGNIFICANTLY
   above the {base_rate:.0f}% baseline (delta > 0.10 or > 0.15):
   - Take the canonical_ids and call find_shared_factors
   - Verify the interventions ARE VARIED (not all the same drug)
   - If interventions vary but the population factor is consistent → you found a hidden driver

3. Once you have a hidden driver candidate:
   - Build the causal chain from FIRST PRINCIPLES
   - Ask: what is biologically different about this subgroup?
   - What does this subgroup have (or lack) that could affect:
     * Insulin signaling
     * Steroidogenesis
     * HPO axis regulation
     * Gut microbiome composition
     * Inflammation
     * Epigenetic programming
   - Drill into the specific nutrient / metabolite / pathway
   - Use pubmed_search and web_search to find mechanistic evidence

4. Rate each discovered pattern by:
   - Strength (how far above baseline is the favorable rate?)
   - Breadth (how many different interventions show the same pattern?)
   - Mechanistic plausibility (does the causal chain make biological sense?)
   - Novelty (is this already known or genuinely overlooked?)

Be obsessive. Follow every thread. The most interesting finding may be the one
where the intervention barely matters but the patient's diet (or BMI, or ethnicity)
predicts the outcome with striking consistency across completely unrelated studies."""


def run_research_agent(
    signal_description: str,
    max_steps: int = DEFAULT_MAX_STEPS,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Run the detective research agent on a given signal.

    verbose=True prints reasoning to console in real time so you can watch it think.
    """

    initial_user_message = (
        f"Our anomaly scanner flagged this. Investigate it as a detective — "
        f"start from the data, not from general knowledge.\n\n"
        f"{signal_description}\n\n"
        f"Start with get_notable_findings and graph_query on this entity. "
        f"Then use fetch_abstract on the specific canonical_ids listed. "
        f"Follow every thread that looks unusual. Don't summarize known facts — "
        f"find what nobody has connected yet."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": initial_user_message},
    ]

    investigation_steps = []
    tool_calls_used = []
    step = 0
    consecutive_no_tool = 0  # track if agent keeps reasoning without tools
    signals_investigated = 0  # how many distinct signals/angles the agent has dug into
    last_tool_results: dict[str, int] = {}  # tool_name -> consecutive_failures

    if verbose:
        print("\n" + "="*70)
        print("RESEARCH AGENT — iniciando investigación")
        print("="*70)
        print(f"SEÑAL: {signal_description[:200]}")
        print("="*70 + "\n")

    log.info("Research agent starting. Signal: %s", signal_description[:100])

    while step < max_steps:
        step += 1
        log.info("Agent step %d / %d", step, max_steps)

        response = _call_ollama_with_tools(messages)
        message = response.get("message", {})
        content = (message.get("content") or "").strip()
        tool_calls = message.get("tool_calls") or []

        # Add assistant message to conversation history
        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        })

        # Print and record reasoning
        if content:
            if verbose:
                print(f"\n--- Paso {step} — Razonamiento del agente ---")
                print(content)
                print()
            investigation_steps.append({
                "step": step,
                "type": "reasoning",
                "content": content,  # full text, no truncation
            })

        if tool_calls:
            consecutive_no_tool = 0
            # Execute each tool call
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                tool_args = func.get("arguments", {})
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                if verbose:
                    print(f"  [HERRAMIENTA] {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:120]})")

                result = _execute_tool_call(tool_name, tool_args)
                tool_calls_used.append(f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)[:80]})")

                # Track consecutive failures per tool so the nudge can warn the agent
                result_parsed = {}
                try:
                    result_parsed = json.loads(result)
                except Exception:
                    pass
                if isinstance(result_parsed, dict) and "error" in result_parsed:
                    last_tool_results[tool_name] = last_tool_results.get(tool_name, 0) + 1
                else:
                    last_tool_results[tool_name] = 0
                    # A successful cross_study_pattern_query or find_shared_factors
                    # counts as opening a new investigation angle
                    if tool_name in ("cross_study_pattern_query", "find_shared_factors",
                                     "get_notable_findings") and "groups" in result:
                        signals_investigated += 1

                if verbose:
                    preview = result[:400] if len(result) > 400 else result
                    print(f"  [RESULTADO] {preview}\n")

                investigation_steps.append({
                    "step": step,
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result,  # full result
                })

                # If a tool has failed 2+ times in a row, inject a redirect nudge
                if last_tool_results.get(tool_name, 0) >= 2:
                    messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tc.get("id", f"call_{step}_{tool_name}"),
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            f"⚠️  '{tool_name}' has failed {last_tool_results[tool_name]} times. "
                            "Stop retrying it. Use sql_query as a direct substitute — "
                            "it can answer any question by querying article_extractions, "
                            "mechanism_links (columns: source_name, relation_type, target_name, confidence), "
                            "entity, article_entity_links, or articles directly. "
                            "Move forward with the investigation."
                        ),
                    })
                    last_tool_results[tool_name] = 0  # reset after nudge
                else:
                    # Normal path: feed result back into conversation
                    messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tc.get("id", f"call_{step}_{tool_name}"),
                    })

        else:
            # No tool call — agent is either reasoning or done
            consecutive_no_tool += 1
            steps_remaining = max_steps - step

            # If the agent hasn't used tools yet (very early steps), nudge it
            if step <= 3 and len(tool_calls_used) == 0:
                messages.append({
                    "role": "user",
                    "content": (
                        "Interesting initial thinking. Now start using your tools — "
                        "search the database, run some SQL queries, look at the actual evidence. "
                        "What's the first thing you want to look up?"
                    ),
                })
                consecutive_no_tool = 0

            # Agent is idle but has plenty of steps left — push it to keep going
            elif consecutive_no_tool == 1 and steps_remaining > 4:
                next_hint = (
                    "You've investigated one signal. "
                    f"You still have {steps_remaining} steps. "
                    "Do NOT repeat the same conclusion. Pick the NEXT unexplored angle:\n"
                    "- A different population variable (population_bmi? population_comorbidities?)\n"
                    "- A Tipo 1 cross-indication signal from the scan (curcumin, genistein, sildenafil+melatonin?)\n"
                    "- A Tipo 4 hidden gem that looks mechanistically interesting\n"
                    "- Use graph_query or sql_query on mechanism_links to verify your causal chain\n"
                    "  (mechanism_links columns: source_name, relation_type, target_name, confidence, canonical_id)\n"
                    "Keep digging. You are not done."
                )
                messages.append({"role": "user", "content": next_hint})
                consecutive_no_tool = 0

            # Two consecutive idle steps and few steps left — actually done
            elif consecutive_no_tool >= 3 or step >= max_steps - 1:
                log.info("Agent concluding at step %d (no tool calls for %d steps)",
                         step, consecutive_no_tool)
                break

    # Ask for final structured research note
    if verbose:
        print("\n" + "="*70)
        print("SOLICITANDO NOTA DE INVESTIGACIÓN FINAL...")
        print("="*70 + "\n")

    conclusion_request = {
        "role": "user",
        "content": (
            "Excellent investigation. Now write your final research note. "
            "First, write freely in natural language — your conclusion, the mechanistic "
            "hypothesis, the quality of the evidence you found, and what experiment "
            "would definitively test this.\n\n"
            "Then, at the very end, output a JSON block (between ```json and ```) with:\n"
            "{\n"
            '  "conclusion": "one paragraph summary",\n'
            '  "mechanistic_hypothesis": "the proposed biological mechanism",\n'
            '  "plausibility_score": 0.0-1.0,\n'
            '  "key_evidence": ["finding 1", "finding 2", ...],\n'
            '  "proposed_experiment": "what study would confirm/refute this",\n'
            '  "research_gaps": ["gap1", "gap2", ...]\n'
            "}"
        ),
    }

    # Keep system + first user message + last 10 messages + conclusion request.
    # This preserves conversation structure while fitting in smaller context windows.
    system_msgs = [m for m in messages if m.get("role") == "system"]
    first_user  = next((m for m in messages if m.get("role") == "user"), None)
    recent      = messages[-10:] if len(messages) > 12 else messages[1:]
    conclusion_messages = system_msgs + ([first_user] if first_user else []) + recent + [conclusion_request]

    final_response = _call_ollama_with_tools(conclusion_messages)
    final_content = (final_response.get("message", {}).get("content") or "").strip()

    if verbose:
        print("\n--- NOTA FINAL DEL AGENTE ---")
        print(final_content)
        print()

    # Parse the JSON block from the final note
    conclusion_data: dict = {}
    import re as _re
    json_match = _re.search(r"```json\s*(.*?)\s*```", final_content, _re.DOTALL)
    if json_match:
        try:
            conclusion_data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    if not conclusion_data:
        # Fallback: try parsing the whole thing as JSON
        try:
            stripped = final_content.strip().lstrip("```json").rstrip("```").strip()
            conclusion_data = json.loads(stripped)
        except json.JSONDecodeError:
            conclusion_data = {
                "conclusion": final_content,
                "mechanistic_hypothesis": "",
                "plausibility_score": None,
                "key_evidence": [],
                "proposed_experiment": "",
                "research_gaps": [],
            }

    return {
        "signal": signal_description,
        "investigation_steps": investigation_steps,
        "tool_calls_used": tool_calls_used,
        "final_note": final_content,
        "conclusion": conclusion_data.get("conclusion", ""),
        "mechanistic_hypothesis": conclusion_data.get("mechanistic_hypothesis", ""),
        "plausibility_score": conclusion_data.get("plausibility_score"),
        "key_evidence": conclusion_data.get("key_evidence", []),
        "proposed_experiment": conclusion_data.get("proposed_experiment", ""),
        "research_gaps": conclusion_data.get("research_gaps", []),
        "steps_taken": step,
        "tools_used_count": len(tool_calls_used),
    }


def _write_agent_report(result: dict, out_path: Path) -> None:
    """Write the full agent investigation as a readable markdown research note."""
    score_val = result.get("plausibility_score")
    score_str = f"{score_val:.2f}" if score_val is not None else "N/A"

    lines = [
        "# Nota de Investigación — Research Agent PCOS",
        "",
        f"**Señal investigada:** {result['signal']}",
        "",
        f"**Pasos de investigación:** {result.get('steps_taken', 0)}  |  "
        f"**Herramientas usadas:** {result.get('tools_used_count', 0)}  |  "
        f"**Plausibilidad:** {score_str}",
        "",
        "---",
        "",
        "## Nota final del agente (texto completo)",
        "",
        result.get("final_note", "_No generada_"),
        "",
        "---",
        "",
        "## Resumen estructurado",
        "",
        f"**Conclusión:** {result.get('conclusion', 'N/A')}",
        "",
        f"**Hipótesis mecanística:** {result.get('mechanistic_hypothesis', 'N/A')}",
        "",
        f"**Experimento propuesto:** {result.get('proposed_experiment', 'N/A')}",
        "",
        "**Evidencia clave encontrada:**",
    ]
    for ev in result.get("key_evidence", []):
        lines.append(f"- {ev}")
    lines += ["", "**Gaps de investigación:**"]
    for gap in result.get("research_gaps", []):
        lines.append(f"- {gap}")

    lines += [
        "",
        "---",
        "",
        f"## Transcripción completa ({result.get('steps_taken', 0)} pasos)",
        "",
    ]
    for s in result.get("investigation_steps", []):
        if s["type"] == "reasoning":
            lines += [
                f"### Paso {s['step']} — Razonamiento",
                "",
                s["content"],  # full text
                "",
            ]
        elif s["type"] == "tool_call":
            result_preview = s.get("result", s.get("result_preview", ""))[:600]
            lines += [
                f"### Paso {s['step']} — Herramienta: `{s['tool']}`",
                "",
                f"**Argumentos:** `{json.dumps(s['args'], ensure_ascii=False)[:150]}`",
                "",
                f"**Resultado:**",
                "```",
                result_preview,
                "```",
                "",
            ]

    lines += ["---", "", "## Herramientas utilizadas", ""]
    for tc in result.get("tool_calls_used", []):
        lines.append(f"- `{tc}`")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PCOS Research Agent — autonomous signal investigator"
    )
    parser.add_argument(
        "--find-patterns", action="store_true",
        help=(
            "Pattern-mining mode: mine ALL population variables for hidden cross-study modifiers. "
            "No specific entity needed — the agent discovers what makes ANY intervention work better."
        )
    )
    parser.add_argument(
        "--from-scan", action="store_true",
        help="Pull top signals from intervention_signals and investigate them (data-driven mode)"
    )
    parser.add_argument(
        "--top-k", type=int, default=3,
        help="Number of top signals to investigate when using --from-scan (default: 3)"
    )
    parser.add_argument(
        "--signal", type=str, default=None,
        help="Free-text signal description to investigate"
    )
    parser.add_argument(
        "--entity", type=str, default=None,
        help="Entity/drug name — builds a data-rich signal from DB stats (better than --signal)"
    )
    parser.add_argument(
        "--max-steps", type=int, default=DEFAULT_MAX_STEPS,
        help=f"Maximum reasoning steps per investigation (default: {DEFAULT_MAX_STEPS})"
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help="Output report path (default: reports/research_agent_<name>.md)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Don't print reasoning to console (only save to file)"
    )
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.find_patterns and not args.from_scan and not args.signal and not args.entity:
        parser.error("Provide --find-patterns, --from-scan, --entity, or --signal")

    # ── Mode 0: pattern mining (the heavy mode) ───────────────────────────────
    if args.find_patterns:
        log.info("Pattern-mining mode: hunting hidden cross-study modifiers...")
        signal_text = _build_pattern_mining_signal()
        result = run_research_agent(
            signal_text,
            max_steps=args.max_steps or 16,  # needs more steps for this
            verbose=not args.quiet,
        )
        out_path = Path(args.out) if args.out else REPORTS_DIR / "research_agent_pattern_mining.md"
        _write_agent_report(result, out_path)
        score_val = result.get("plausibility_score")
        score_str = f"{score_val:.2f}" if score_val is not None else "N/A"
        print(f"\n{'='*60}")
        print(f"PATTERN MINING COMPLETO")
        print(f"  Plausibilidad: {score_str}  |  Pasos: {result.get('steps_taken')}  |  Tools: {result.get('tools_used_count', 0)}")
        print(f"  Reporte: {out_path}")
        print(f"{'='*60}")

    # ── Mode 1: data-driven scan (recommended) ────────────────────────────────
    elif args.from_scan:
        log.info("Loading top %d signals from intervention_signals...", args.top_k)
        signals = _load_top_signals_from_db(top_k=args.top_k)
        if not signals:
            log.error("No signals found in DB. Run anomaly_scan_v2.py first.")
            raise SystemExit(1)

        log.info("Found %d signals. Investigating each...", len(signals))
        for i, sig_data in enumerate(signals, 1):
            name = sig_data.get("canonical_name", f"signal_{i}")
            log.info("=== INVESTIGATING SIGNAL %d/%d: %s ===", i, len(signals), name)
            signal_text = _build_structured_signal(sig_data)
            result = run_research_agent(signal_text, max_steps=args.max_steps, verbose=not args.quiet)
            safe_name = name.replace(" ", "_").replace("/", "-")
            out_path = Path(args.out) if args.out else REPORTS_DIR / f"research_agent_{safe_name}.md"
            _write_agent_report(result, out_path)
            score_val = result.get("plausibility_score")
            score_str = f"{score_val:.2f}" if score_val is not None else "N/A"
            print(f"\n{'='*60}")
            print(f"SEÑAL {i}/{len(signals)}: {name}")
            print(f"  Plausibilidad: {score_str}  |  Pasos: {result.get('steps_taken')}  |  Tools: {result.get('tools_used_count', 0)}")
            print(f"  Reporte: {out_path}")
            print(f"{'='*60}")

    # ── Mode 2: entity-driven (pulls real stats from DB) ──────────────────────
    elif args.entity:
        log.info("Building data-rich signal for entity: %s", args.entity)
        # Try to find the entity in intervention_signals
        signals = _load_top_signals_from_db(top_k=50)
        entity_lower = args.entity.lower()
        sig_data = next(
            (s for s in signals if entity_lower in s.get("canonical_name", "").lower()),
            None,
        )
        if sig_data:
            signal_text = _build_structured_signal(sig_data)
            log.info("Found DB signal data for '%s' — using structured signal", args.entity)
        else:
            # Entity not in intervention_signals — build minimal signal from DB
            log.warning("'%s' not found in intervention_signals — building minimal signal", args.entity)
            sig_data = {
                "canonical_name": args.entity,
                "entity_type": "unknown",
                "n_studies": 0,
                "n_favorable": 0,
                "n_neutral": 0,
                "n_unfavorable": 0,
                "consistency_score": 0.0,
                "weighted_score": 0.0,
                "signal_type": "manual",
                "anomaly_reason": "Manually requested investigation",
                "supporting_articles": [],
                "kg_triples": [],
                "notable_findings": [],
            }
            signal_text = _build_structured_signal(sig_data)

        result = run_research_agent(signal_text, max_steps=args.max_steps, verbose=not args.quiet)
        safe_name = args.entity.replace(" ", "_").replace("/", "-")
        out_path = Path(args.out) if args.out else REPORTS_DIR / f"research_agent_{safe_name}.md"
        _write_agent_report(result, out_path)
        score_val = result.get("plausibility_score")
        score_str = f"{score_val:.2f}" if score_val is not None else "N/A"
        print(f"\n{'='*60}")
        print(f"INVESTIGACION COMPLETA: {args.entity}")
        print(f"  Plausibilidad: {score_str}  |  Pasos: {result.get('steps_taken')}  |  Tools: {result.get('tools_used_count', 0)}")
        print(f"  Reporte: {out_path}")
        print(f"{'='*60}")

    # ── Mode 3: free-text signal (legacy) ─────────────────────────────────────
    else:
        result = run_research_agent(args.signal, max_steps=args.max_steps, verbose=not args.quiet)
        out_path = Path(args.out) if args.out else REPORTS_DIR / "research_agent_latest.md"
        _write_agent_report(result, out_path)
        score_val = result.get("plausibility_score")
        score_str = f"{score_val:.2f}" if score_val is not None else "N/A"
        print(f"\n{'='*60}")
        print(f"INVESTIGACION COMPLETA")
        print(f"  Plausibilidad: {score_str}  |  Pasos: {result.get('steps_taken')}  |  Tools: {result.get('tools_used_count', 0)}")
        print(f"  Reporte: {out_path}")
        print(f"{'='*60}")
