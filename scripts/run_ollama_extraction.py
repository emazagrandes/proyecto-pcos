import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

from config import PROCESSED_DIR, REPORTS_DIR
from llm_support import (
    EXTRACTION_SCHEMA_VERSION, empty_extraction_record,
    EXTRACTION_FIELDS, SYSTEM_PROMPT, build_extraction_prompt,
)


DEFAULT_TOP_K = 200
DEFAULT_MODEL = "gemma4:31b-cloud"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
EXTRACTOR_PREFIX = "ollama"
PROMPT_VERSION = "schema-1.3-mechanisms"
MAX_SUMMARY_CHARS = 600
MAX_ABSTRACT_CHARS = 1400
MAX_URL_CHARS = 200


def _trim_text(value: Any, limit: int) -> str | None:
    if value in (None, "", "[]"):
        return None
    text = str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _load_candidates(conn: sqlite3.Connection, top_k: int,
                     skip_extracted: bool = True) -> pd.DataFrame:
    """
    Load articles to extract, with smart prioritization:
      1. Tier 1 / Tier 2 articles (LLM-labeled) that are RCT or meta-analysis
      2. Other tier 1 / tier 2 labeled articles
      3. Articles with RCT/trial in study_type (raw field, catches trials)
      4. Remaining by evidence_score

    This ensures RCTs and trials aren't buried by review articles
    even when they have lower citation-based evidence_score.
    """
    already_done = ""
    if skip_extracted:
        already_done = """
            AND a.canonical_id NOT IN (
                SELECT canonical_id FROM article_extractions
                WHERE extraction_status NOT IN ('error', 'ollama_dry_run')
            )
        """

    query = f"""
        SELECT
            a.canonical_id, a.title, a.journal, a.year,
            a.study_type, a.evidence_tier, a.evidence_score,
            a.summary_short, a.abstract_text, a.url,
            -- fulltext fields (NULL if not fetched yet)
            ft.fetch_source,
            ft.abstract_full   AS ft_abstract_full,
            ft.methods_text    AS ft_methods_text,
            ft.results_text    AS ft_results_text,
            ft.discussion_text AS ft_discussion_text,
            -- priority score: higher = processed first
            CASE
                -- Tier 1/2 RCTs and meta-analyses: top priority
                WHEN l.evidence_tier_llm IN ('tier_1','tier_2')
                 AND l.study_type_llm IN ('rct','rct_or_trial','meta_analysis','meta-analysis','guideline')
                THEN 4
                -- Tier 1/2 any study type
                WHEN l.evidence_tier_llm IN ('tier_1','tier_2')
                THEN 3
                -- RCT/trial in raw study_type field (catches unlabeled trials)
                WHEN LOWER(a.study_type) LIKE '%rct%'
                  OR LOWER(a.study_type) LIKE '%trial%'
                  OR LOWER(a.study_type) LIKE '%meta%'
                THEN 2
                -- Everything else by evidence_score
                ELSE 1
            END AS priority
        FROM articles a
        LEFT JOIN article_llm_labels l ON a.canonical_id = l.canonical_id
        LEFT JOIN article_fulltexts ft
               ON a.canonical_id = ft.canonical_id
              AND ft.fetch_status = 'ok'
        WHERE a.llm_ready = 1
          AND a.abstract_text IS NOT NULL
          AND LENGTH(a.abstract_text) > 100
          {already_done}
        ORDER BY priority DESC, a.evidence_score DESC, a.year DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(top_k,))
    # Log priority breakdown
    if len(df) > 0 and 'priority' in df.columns:
        counts = df['priority'].value_counts().sort_index(ascending=False)
        log.info("Priority breakdown: %s",
                 " | ".join(f"P{p}={n}" for p, n in counts.items()))
    return df.drop(columns=['priority'], errors='ignore')


def _build_prompt(row: pd.Series) -> tuple[str, bool]:
    """
    Build extraction prompt using the canonical builder from llm_support.
    Returns (prompt_text, has_fulltext).

    Extracts fulltext fields from the row (prefixed ft_*) and passes them
    to build_extraction_prompt so Methods/Results sections are included.
    """
    row_dict = row.to_dict()
    fulltext: dict | None = None
    if row_dict.get("fetch_source"):
        fulltext = {
            "fetch_source":   row_dict.pop("fetch_source", None),
            "abstract_full":  row_dict.pop("ft_abstract_full", None),
            "methods_text":   row_dict.pop("ft_methods_text", None),
            "results_text":   row_dict.pop("ft_results_text", None),
            "discussion_text": row_dict.pop("ft_discussion_text", None),
        }
        has_fulltext = any(
            fulltext.get(k) for k in ("methods_text", "results_text", "abstract_full")
        )
    else:
        # Remove ft_ columns even if None so they don't clutter source_payload
        for k in ("fetch_source", "ft_abstract_full", "ft_methods_text",
                  "ft_results_text", "ft_discussion_text"):
            row_dict.pop(k, None)
        has_fulltext = False

    return build_extraction_prompt(row_dict, fulltext=fulltext), has_fulltext


def _strip_markdown_json(text: str) -> str:
    """Elimina bloques de markdown y tags <think>...</think> de modelos en modo reasoning."""
    import re as _re
    text = text.strip()
    # Strip <think>...</think> blocks (Gemma reasoning mode)
    text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _call_ollama(model: str, prompt: str, timeout_s: int,
                 max_retries: int = 3, has_fulltext: bool = False) -> tuple[dict[str, Any], str]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 1400,   # schema v1.3 with mechanisms needs ~1000-1300 tokens
            # With fulltext (Methods ~2500 + Results ~2000 + Discussion ~1500) we
            # need ~16k tokens; without fulltext 8k is enough.
            "num_ctx": 16384 if has_fulltext else 8192,
        },
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout_s)
            resp.raise_for_status()
            body = resp.json()
            content = _strip_markdown_json(((body.get("message") or {}).get("content") or "").strip())
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                repaired = content.rstrip().rstrip(",")
                if not repaired.endswith("}"):
                    repaired += "}"
                try:
                    parsed = json.loads(repaired)
                except json.JSONDecodeError:
                    raise json.JSONDecodeError(
                        f"JSON irreparable. Primeros 200 chars: {content[:200]}", content, 0
                    )
            return parsed, content
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            wait = 2 ** attempt
            log.warning("Timeout/connection error (attempt %d/%d): %s. Retrying in %ds...",
                        attempt, max_retries, e.__class__.__name__, wait)
            time.sleep(wait)
        except json.JSONDecodeError as e:
            if attempt < max_retries:
                log.warning("Empty/bad JSON from Ollama (attempt %d/%d): %s. Retrying in 5s...",
                            attempt, max_retries, str(e)[:80])
                time.sleep(5)
            else:
                raise
    raise RuntimeError(f"Ollama call failed after {max_retries} retries")


def _normalize_response(canonical_id: str, response: dict[str, Any]) -> dict[str, Any]:
    record = empty_extraction_record(canonical_id)
    for key in record.keys():
        if key in response:
            record[key] = response[key]
    record["schema_version"] = EXTRACTION_SCHEMA_VERSION
    record["canonical_id"] = canonical_id
    if record.get("effect_direction") not in {"favorable", "neutral", "unfavorable", "mixed", "unclear"}:
        record["effect_direction"] = "unclear"
    if record.get("main_outcomes") is None:
        record["main_outcomes"] = []
    if record.get("limitations") is None:
        record["limitations"] = []
    if record.get("population_comorbidities") is None:
        record["population_comorbidities"] = []
    return record


def _ensure_schema_migrations(conn: sqlite3.Connection) -> None:
    """Idempotent migrations: add new columns and tables as the schema evolves."""
    # notable_finding column
    try:
        conn.execute("ALTER TABLE article_extractions ADD COLUMN notable_finding TEXT")
    except sqlite3.OperationalError:
        pass

    # mechanism_links table (knowledge graph edges) — no restrictive CHECKs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mechanism_links (
            link_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_id      TEXT REFERENCES articles(canonical_id),
            source_name       TEXT NOT NULL,
            source_type       TEXT NOT NULL DEFAULT 'entity',
            relation_type     TEXT NOT NULL,
            target_name       TEXT NOT NULL,
            target_type       TEXT NOT NULL DEFAULT 'entity',
            confidence        REAL DEFAULT 0.7,
            extraction_method TEXT DEFAULT 'llm_extraction',
            raw_snippet       TEXT,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ml_source ON mechanism_links(source_name)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ml_target ON mechanism_links(target_name)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ml_canonical ON mechanism_links(canonical_id)
    """)
    conn.commit()


def _save_mechanisms(
    conn: sqlite3.Connection,
    canonical_id: str,
    mechanisms: list[dict],
) -> int:
    """
    Write mechanism triples extracted by Gemma into mechanism_links.
    Deletes existing LLM-extracted links for this article first (idempotent).
    Returns number of triples saved.
    """
    if not mechanisms:
        return 0

    conn.execute("""
        DELETE FROM mechanism_links
        WHERE canonical_id = ? AND extraction_method = 'llm_extraction'
    """, (canonical_id,))

    saved = 0
    for triple in mechanisms:
        source = (triple.get("source") or "").strip().lower()
        relation = (triple.get("relation") or "").strip().lower()
        target = (triple.get("target") or "").strip().lower()
        confidence = float(triple.get("confidence", 0.7))

        valid_relations = {
            "activates", "inhibits", "improves", "reduces", "increases",
            "associated_with", "indicates", "tested_in",
        }
        if not source or not target or relation not in valid_relations:
            continue
        if confidence < 0.4:
            continue

        conn.execute("""
            INSERT INTO mechanism_links
                (canonical_id, source_name, source_type, relation_type,
                 target_name, target_type, confidence, extraction_method)
            VALUES (?, ?, 'entity', ?, ?, 'entity', ?, 'llm_extraction')
        """, (canonical_id, source, relation, target, confidence))
        saved += 1

    return saved


def _upsert_extraction(
    conn: sqlite3.Connection,
    extraction: dict[str, Any],
    source_payload: dict[str, Any],
    raw_response: str,
    model: str,
    status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO article_extractions (
            canonical_id, schema_version, extraction_status, extractor_name, prompt_version,
            population, population_diet, population_bmi, population_age_range,
            population_comorbidities, population_ethnicity,
            n_total, intervention, comparator, main_outcomes, effect_direction,
            limitations, reasoning_summary, notable_finding,
            source_payload, raw_response, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_id) DO UPDATE SET
            schema_version=excluded.schema_version,
            extraction_status=excluded.extraction_status,
            extractor_name=excluded.extractor_name,
            prompt_version=excluded.prompt_version,
            population=excluded.population,
            population_diet=excluded.population_diet,
            population_bmi=excluded.population_bmi,
            population_age_range=excluded.population_age_range,
            population_comorbidities=excluded.population_comorbidities,
            population_ethnicity=excluded.population_ethnicity,
            n_total=excluded.n_total,
            intervention=excluded.intervention,
            comparator=excluded.comparator,
            main_outcomes=excluded.main_outcomes,
            effect_direction=excluded.effect_direction,
            limitations=excluded.limitations,
            reasoning_summary=excluded.reasoning_summary,
            notable_finding=excluded.notable_finding,
            source_payload=excluded.source_payload,
            raw_response=excluded.raw_response,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            extraction["canonical_id"],
            extraction["schema_version"],
            status,
            f"{EXTRACTOR_PREFIX}_{model}",
            PROMPT_VERSION,
            extraction.get("population"),
            extraction.get("population_diet"),
            extraction.get("population_bmi"),
            extraction.get("population_age_range"),
            json.dumps(extraction.get("population_comorbidities", []), ensure_ascii=False),
            extraction.get("population_ethnicity"),
            extraction.get("n_total"),
            extraction.get("intervention"),
            extraction.get("comparator"),
            json.dumps(extraction.get("main_outcomes", []), ensure_ascii=False),
            extraction.get("effect_direction"),
            json.dumps(extraction.get("limitations", []), ensure_ascii=False),
            extraction.get("reasoning_summary"),
            extraction.get("notable_finding"),
            json.dumps(source_payload, ensure_ascii=False),
            raw_response,
        ),
    )


def _write_report(results: list[dict[str, Any]], model: str, dry_run: bool) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "ollama_extraction_report.md"
    df = pd.DataFrame(results)
    lines = [
        "# Ollama Extraction Report",
        "",
        f"- Model: {model}",
        f"- Dry run: {dry_run}",
        f"- Prompt version: {PROMPT_VERSION}",
        f"- Registros procesados: {len(results)}",
        "",
        "## Cobertura",
        "",
    ]
    if not df.empty:
        for field in ("population", "population_diet", "population_bmi",
                      "population_age_range", "population_ethnicity",
                      "n_total", "intervention", "comparator"):
            if field in df.columns:
                lines.append(f"- {field}: {int(df[field].notna().sum())}/{len(df)}")
        for list_field in ("main_outcomes", "population_comorbidities"):
            if list_field in df.columns:
                lines.append(f"- {list_field}: {int(df[list_field].map(bool).sum())}/{len(df)}")
    lines.extend(["", "## Ejemplos", ""])
    for record in results[:5]:
        lines.append(f"### {record['canonical_id']}")
        lines.append(f"- intervention: {record.get('intervention')}")
        lines.append(f"- comparator: {record.get('comparator')}")
        lines.append(f"- effect_direction: {record.get('effect_direction')}")
        lines.append(f"- outcomes: {', '.join(record.get('main_outcomes', [])) or 'none'}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_ollama_extraction(top_k: int, model: str, timeout_s: int,
                          dry_run: bool, skip_extracted: bool = True) -> tuple[Path, Path]:
    db_path = PROCESSED_DIR / "pcos_research.db"
    out_path = PROCESSED_DIR / "ollama_article_extractions.jsonl"
    if not db_path.exists():
        out_path.write_text("", encoding="utf-8")
        report_path = _write_report([], model, dry_run)
        return out_path, report_path

    with sqlite3.connect(db_path, timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        _ensure_schema_migrations(conn)
        articles = _load_candidates(conn, top_k=top_k, skip_extracted=skip_extracted)
        log.info("Candidates to extract: %d (skip_extracted=%s)", len(articles), skip_extracted)
        results: list[dict[str, Any]] = []
        errors = 0

        for i, (_, row) in enumerate(articles.iterrows(), 1):
            source_payload = row.to_dict()
            canonical_id = source_payload["canonical_id"]

            if i % 10 == 0 or i == 1:
                log.info("Progress: %d / %d  (errors so far: %d)", i, len(articles), errors)

            try:
                if dry_run:
                    extraction = empty_extraction_record(canonical_id)
                    extraction["reasoning_summary"] = "Dry run: prompt generated but model not called."
                    raw_response = json.dumps(extraction, ensure_ascii=False)
                    status = "ollama_dry_run"
                else:
                    prompt, has_fulltext = _build_prompt(row)
                    parsed, raw_response = _call_ollama(
                        model=model, prompt=prompt, timeout_s=timeout_s,
                        has_fulltext=has_fulltext,
                    )
                    extraction = _normalize_response(canonical_id, parsed)
                    status = "ollama_generated"

                _upsert_extraction(conn, extraction, source_payload, raw_response, model, status)

                # Write mechanism triples to knowledge graph
                mechanisms = extraction.get("mechanisms") or []
                if isinstance(mechanisms, list) and mechanisms:
                    n_saved = _save_mechanisms(conn, canonical_id, mechanisms)
                    if n_saved:
                        log.debug("KG: saved %d triples for %s", n_saved, canonical_id)

                results.append(extraction)

                # Commit every 20 to survive crashes
                if i % 20 == 0:
                    conn.commit()

            except Exception as e:
                errors += 1
                log.warning("Error on %s: %s", canonical_id, e)
                # Save error record so we know it failed (won't retry unless --re-extract-errors)
                err_extraction = empty_extraction_record(canonical_id)
                err_extraction["reasoning_summary"] = f"Extraction error: {e}"
                # Retry DB write up to 3× if locked
                for _db_attempt in range(3):
                    try:
                        _upsert_extraction(conn, err_extraction, source_payload,
                                           str(e), model, "error")
                        break
                    except sqlite3.OperationalError as dbe:
                        if "locked" in str(dbe).lower() and _db_attempt < 2:
                            log.warning("DB locked writing error record, retry %d/3...", _db_attempt + 1)
                            time.sleep(10)
                        else:
                            log.error("Could not write error record for %s: %s", canonical_id, dbe)
                            break
                if errors > 100:
                    log.error("Too many errors (%d), stopping.", errors)
                    break

        conn.commit()
        log.info("Done. Extracted: %d  Errors: %d", len(results), errors)

    with out_path.open("w", encoding="utf-8", errors="replace") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report_path = _write_report(results, model, dry_run)
    return out_path, report_path


def run_repopulate_pop_fields(top_k: int, model: str, timeout_s: int) -> None:
    """
    Re-extract ONLY articles where population sub-fields (bmi, diet, ethnicity,
    age_range) are mostly NULL, using the improved prompt that includes field guidance.

    Overwrites only the population_* fields in existing extractions — keeps
    intervention, comparator, effect_direction, outcomes intact.
    """
    db_path = PROCESSED_DIR / "pcos_research.db"
    with sqlite3.connect(db_path, timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        _ensure_schema_migrations(conn)

        # Articles with extraction but missing population sub-fields
        rows = conn.execute(f"""
            SELECT a.canonical_id, a.title, a.journal, a.year,
                   a.study_type, a.evidence_tier, a.evidence_score,
                   a.summary_short, a.abstract_text, a.url
            FROM articles a
            JOIN article_extractions ae ON a.canonical_id = ae.canonical_id
            WHERE ae.extraction_status = 'ollama_generated'
              AND (ae.population_bmi IS NULL OR ae.population_ethnicity IS NULL)
              AND a.abstract_text IS NOT NULL
              AND length(a.abstract_text) > 100
            ORDER BY a.evidence_score DESC NULLS LAST
            LIMIT {top_k}
        """).fetchall()

        cols = ["canonical_id","title","journal","year","study_type",
                "evidence_tier","evidence_score","summary_short","abstract_text","url"]
        import pandas as pd
        articles = pd.DataFrame(rows, columns=cols)

        log.info("Articles to repopulate pop fields: %d", len(articles))
        updated = 0

        for i, (_, row) in enumerate(articles.iterrows(), 1):
            canonical_id = row["canonical_id"]
            if i % 10 == 0:
                log.info("Progress: %d / %d", i, len(articles))
            try:
                prompt, has_fulltext = _build_prompt(row)
                parsed, _ = _call_ollama(model=model, prompt=prompt, timeout_s=timeout_s,
                                         has_fulltext=has_fulltext)
                extraction = _normalize_response(canonical_id, parsed)

                # Only update population sub-fields, not core fields
                conn.execute("""
                    UPDATE article_extractions
                    SET population_bmi        = ?,
                        population_diet       = ?,
                        population_ethnicity  = ?,
                        population_age_range  = ?,
                        population_comorbidities = ?,
                        prompt_version        = ?,
                        updated_at            = CURRENT_TIMESTAMP
                    WHERE canonical_id = ?
                """, (
                    extraction.get("population_bmi"),
                    extraction.get("population_diet"),
                    extraction.get("population_ethnicity"),
                    extraction.get("population_age_range"),
                    json.dumps(extraction.get("population_comorbidities", [])),
                    "schema-1.1-pop-v2",
                    canonical_id,
                ))
                updated += 1
                if updated % 20 == 0:
                    conn.commit()
                    log.info("Committed %d updates", updated)
            except Exception as e:
                log.warning("Error on %s: %s", canonical_id, e)

        conn.commit()
        log.info("Done. Updated population fields for %d articles.", updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K,
                        help="Max articles to extract in this run")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-s", type=int, default=240)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--re-extract", action="store_true",
                        help="Re-extract articles already done (default: skip them)")
    parser.add_argument("--repopulate-pop-fields", action="store_true",
                        help="Re-run only articles with NULL population sub-fields "
                             "(bmi, diet, ethnicity, age_range) using improved prompt")
    args = parser.parse_args()

    if args.repopulate_pop_fields:
        run_repopulate_pop_fields(
            top_k=args.top_k,
            model=args.model,
            timeout_s=args.timeout_s,
        )
    else:
        data_path, report_path = run_ollama_extraction(
            top_k=args.top_k,
            model=args.model,
            timeout_s=args.timeout_s,
            dry_run=args.dry_run,
            skip_extracted=not args.re_extract,
        )
        print(f"Ollama extractions: {data_path}")
        print(f"Ollama extraction report: {report_path}")
