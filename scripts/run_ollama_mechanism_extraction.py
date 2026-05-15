"""
run_ollama_mechanism_extraction.py
====================================
Extrae relaciones mecanísticas de abstracts usando Gemma 4 via Ollama.
Escribe filas en la tabla mechanism_links.

Cada abstract produce 0–N relaciones tipadas:
    intervention --INHIBITS--> mechanism
    mechanism    --REDUCES-->  biomarker
    biomarker    --INDICATES-> comorbidity
    ...

Run:
    python scripts/run_ollama_mechanism_extraction.py [--limit N] [--reset]
    --limit N   procesar solo N artículos (útil para pruebas)
    --reset     borrar todos los links extraídos por LLM y empezar de cero
"""

import sqlite3
import json
import time
import argparse
import requests
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH   = Path("data/processed/pcos_research.db")
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL     = "gemma4:31b-cloud"

VALID_SOURCE_TYPES = {
    "intervention", "mechanism", "biomarker", "outcome",
    "comorbidity", "phenotype", "diagnostic_test",
}
VALID_TARGET_TYPES = VALID_SOURCE_TYPES
VALID_RELATIONS = {
    "activates", "inhibits", "improves", "reduces",
    "indicates", "associated_with", "measures", "tested_in",
}

SYSTEM_PROMPT = """You are a biomedical knowledge extraction assistant specialized in PCOS research.
Your task: read a scientific abstract and extract mechanistic relationships.
Return ONLY valid JSON, no explanation."""

USER_TEMPLATE = """Abstract:
{abstract}

Extract mechanistic relationships from this abstract. Return JSON:
{{
  "relations": [
    {{
      "source_type": "intervention",
      "source_name": "silibinin",
      "relation_type": "inhibits",
      "target_type": "mechanism",
      "target_name": "NF-kB pathway",
      "direction": "positive",
      "confidence": 0.85,
      "raw_snippet": "silibinin significantly inhibited NF-κB activation"
    }}
  ]
}}

Rules:
- source_type / target_type must be one of: intervention, mechanism, biomarker, outcome, comorbidity, phenotype, diagnostic_test
- relation_type must be one of: activates, inhibits, improves, reduces, indicates, associated_with, measures, tested_in
- direction: positive (beneficial for PCOS), negative (harmful), neutral, unclear
- confidence: 0.0–1.0 based on how explicit the text is
- raw_snippet: the exact phrase from the abstract supporting this relation
- Use canonical English names (lowercase). PCOS = PCOS, not "polycystic ovary syndrome"
- If no clear mechanistic relation exists, return: {{"relations": []}}
- Extract at most 5 relations. Prefer the most specific and well-supported ones.
"""


def _parse_json_from_response(text: str) -> dict:
    """Extract JSON from Gemma response, handling markdown code blocks."""
    text = text.strip()
    # Strip ```json ... ``` wrapper if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = inner.strip()
    return json.loads(text)


def call_gemma(abstract: str) -> list[dict]:
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": USER_TEMPLATE.format(abstract=abstract[:3000])},
        ],
        "options": {"temperature": 0.1, "num_predict": 800},
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        text = r.json()["message"]["content"]
        data = _parse_json_from_response(text)
        return data.get("relations", [])
    except Exception as e:
        print(f"    [WARN] Gemma error: {e}")
        return []


def validate_relation(rel: dict) -> bool:
    """Return True if the relation has valid types and non-empty names."""
    if not rel.get("source_name") or not rel.get("target_name"):
        return False
    if rel.get("source_type") not in VALID_SOURCE_TYPES:
        return False
    if rel.get("target_type") not in VALID_TARGET_TYPES:
        return False
    if rel.get("relation_type") not in VALID_RELATIONS:
        return False
    conf = rel.get("confidence", 0)
    if not isinstance(conf, (int, float)) or conf < 0.3:
        return False  # discard low-confidence extractions
    return True


def upsert_entity_id(conn, name: str, etype: str) -> int | None:
    """Return entity_id if it exists in the entity table, else None."""
    row = conn.execute(
        "SELECT entity_id FROM entity WHERE canonical_name = ?", (name.lower().strip(),)
    ).fetchone()
    return row[0] if row else None


def run(limit: int | None, reset: bool):
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    if reset:
        deleted = conn.execute(
            "DELETE FROM mechanism_links WHERE extraction_method = 'llm'"
        ).rowcount
        conn.commit()
        print(f"[RESET] Deleted {deleted} LLM-extracted links.")

    # Articles that have an abstract and haven't been processed yet
    processed = {
        r[0] for r in conn.execute(
            "SELECT DISTINCT canonical_id FROM mechanism_links WHERE extraction_method = 'llm'"
        ).fetchall()
    }

    # Join with article_extractions so we focus on articles with structured data
    candidates = conn.execute("""
        SELECT a.canonical_id, a.abstract_text
        FROM articles a
        JOIN article_extractions ae ON a.canonical_id = ae.canonical_id
        WHERE a.abstract_text IS NOT NULL
          AND length(a.abstract_text) > 100
        ORDER BY a.canonical_id
    """).fetchall()

    candidates = [(aid, ab) for aid, ab in candidates if aid not in processed]
    if limit:
        candidates = candidates[:limit]

    print(f"Articles to process: {len(candidates)}")
    total_inserted = 0

    for i, (canonical_id, abstract) in enumerate(candidates):
        print(f"[{i+1}/{len(candidates)}] canonical_id={canonical_id} ... ", end="", flush=True)

        relations = call_gemma(abstract)
        valid = [r for r in relations if validate_relation(r)]
        print(f"{len(valid)} relations", end="")

        inserted = 0
        for rel in valid:
            src_id = upsert_entity_id(conn, rel["source_name"], rel["source_type"])
            tgt_id = upsert_entity_id(conn, rel["target_name"], rel["target_type"])

            conn.execute("""
                INSERT INTO mechanism_links
                    (source_type, source_id, source_name,
                     relation_type,
                     target_type, target_id, target_name,
                     canonical_id, confidence, extraction_method, direction, raw_snippet)
                VALUES (?,?,?, ?, ?,?,?, ?,?,?,?,?)
            """, (
                rel["source_type"],   src_id, rel["source_name"].lower().strip(),
                rel["relation_type"],
                rel["target_type"],   tgt_id, rel["target_name"].lower().strip(),
                canonical_id,
                float(rel.get("confidence", 0.5)),
                "llm",
                rel.get("direction", "unclear"),
                rel.get("raw_snippet", ""),
            ))
            inserted += 1

        conn.commit()
        total_inserted += inserted
        print(f" | total so far: {total_inserted}")
        time.sleep(0.1)  # small pause between calls

    final = conn.execute("SELECT COUNT(*) FROM mechanism_links").fetchone()[0]
    conn.close()
    print(f"\nDone. Total mechanism_links in DB: {final}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Max articles to process (default: all pending)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete all LLM-extracted links and reprocess")
    args = parser.parse_args()
    run(args.limit, args.reset)
