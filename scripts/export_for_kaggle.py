"""
export_for_kaggle.py — Exporta artículos pendientes de extracción para procesar en Kaggle.

Genera: data/kaggle_export/articles_to_extract.jsonl

Cada línea = un artículo con abstract + fulltext disponible.
Kaggle lee este JSONL, llama a Gemini, y produce extractions_output.jsonl.
Luego import_from_kaggle.py importa los resultados a SQLite.

Uso:
    python scripts/export_for_kaggle.py --top-k 2000
"""
import argparse, json, sqlite3
from pathlib import Path

DB_PATH     = Path("data/processed/pcos_research.db")
EXPORT_DIR  = Path("data/kaggle_export")
EXPORT_FILE = EXPORT_DIR / "articles_to_extract.jsonl"


def export(top_k: int = 2000, min_utility: float = 0.4):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            a.canonical_id,
            a.title,
            CAST(a.year AS INTEGER) AS year,
            a.journal,
            a.abstract_text,
            a.study_type,
            a.evidence_tier,
            ft.abstract_full,
            ft.methods_text,
            ft.results_text,
            ft.fetch_source,
            COALESCE(l.study_type_llm, '')   AS study_type_llm,
            COALESCE(l.evidence_tier_llm, '') AS evidence_tier_llm,
            COALESCE(l.utility_score_llm, 0.5) AS utility_score
        FROM articles a
        LEFT JOIN article_fulltexts ft ON ft.canonical_id = a.canonical_id
        LEFT JOIN article_llm_labels l  ON l.canonical_id  = a.canonical_id
        WHERE a.canonical_id NOT IN (
            SELECT canonical_id FROM article_extractions
            WHERE extraction_status = 'ollama_generated'
        )
        AND a.abstract_text IS NOT NULL
        AND COALESCE(l.utility_score_llm, 0.5) >= ?
        ORDER BY COALESCE(l.utility_score_llm, 0.5) DESC
        LIMIT ?
    """, (min_utility, top_k)).fetchall()

    conn.close()

    written = 0
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        for row in rows:
            d = dict(row)
            # Build combined text: fulltext if available, else abstract
            text_parts = []
            if d.get("abstract_full"):
                text_parts.append(f"Abstract: {d['abstract_full']}")
            elif d.get("abstract_text"):
                text_parts.append(f"Abstract: {d['abstract_text']}")
            if d.get("methods_text"):
                text_parts.append(f"Methods: {d['methods_text'][:2000]}")
            if d.get("results_text"):
                text_parts.append(f"Results: {d['results_text'][:2000]}")
            d["combined_text"] = "\n\n".join(text_parts)[:6000]
            d["has_fulltext"] = bool(d.get("fetch_source"))
            # Remove raw columns to keep file smaller
            for col in ("abstract_full", "methods_text", "results_text", "abstract_text"):
                d.pop(col, None)
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            written += 1

    size_mb = EXPORT_FILE.stat().st_size / 1e6
    print(f"Exportados: {written} artículos → {EXPORT_FILE} ({size_mb:.1f} MB)")
    print(f"  Con fulltext: {sum(1 for r in rows if dict(r).get('fetch_source'))}")
    print(f"  Solo abstract: {sum(1 for r in rows if not dict(r).get('fetch_source'))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=2000)
    parser.add_argument("--min-utility", type=float, default=0.4)
    args = parser.parse_args()
    export(args.top_k, args.min_utility)
