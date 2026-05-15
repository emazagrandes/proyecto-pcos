"""
build_embeddings.py
-------------------
Convierte todos los artículos de pcos_research.db en vectores (embeddings)
usando nomic-embed-text vía Ollama, y los guarda en ChromaDB.

¿Qué hace exactamente?
  1. Lee artículos de SQLite (título + abstract).
  2. Para cada artículo, llama a Ollama /api/embed → vector de 768 números.
  3. Guarda el vector en ChromaDB junto con metadatos clave.
  4. Es idempotente: si ya existe el embedding para un artículo, lo salta.

Resultado:
  data/processed/chroma_db/   ← base de datos vectorial (archivos en disco)

Uso:
  python scripts/build_embeddings.py              # todos los artículos
  python scripts/build_embeddings.py --batch 500  # solo los primeros 500
  python scripts/build_embeddings.py --dry-run    # sin escribir, solo probar
"""

import argparse
import sqlite3
import time
from pathlib import Path
from typing import Any

import chromadb
import requests

from config import PROCESSED_DIR

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"
CHROMA_DIR = PROCESSED_DIR / "chroma_db"
COLLECTION_NAME = "pcos_articles"

# Tamaño del lote para llamadas a Ollama.
# nomic-embed-text puede procesar varios textos en una sola llamada.
BATCH_SIZE = 10

# Longitud máxima del texto que enviamos al modelo (en caracteres).
# nomic-embed-text soporta hasta ~8000 tokens, pero los abstracts
# de PCOS raramente superan los 2000 caracteres. Truncamos en 3000
# para ser seguros sin perder información relevante.
MAX_TEXT_CHARS = 3000


# ---------------------------------------------------------------------------
# Preparación de texto
# ---------------------------------------------------------------------------
def _build_text(title: Any, abstract: Any) -> str:
    """
    Combina título y abstract en un solo texto para embeddings.

    ¿Por qué combinar?
    El embedding captura el significado del texto completo. Si solo
    usamos el título, perdemos el detalle metodológico del abstract.
    Si solo usamos el abstract, podemos perder palabras clave del título.
    La combinación title + abstract da el mejor vector semántico.
    """
    parts = []
    if title and str(title).strip():
        parts.append(str(title).strip())
    if abstract and str(abstract).strip() not in ("", "[]", "None"):
        parts.append(str(abstract).strip())
    text = " ".join(parts)
    # Truncar si es demasiado largo
    return text[:MAX_TEXT_CHARS] if len(text) > MAX_TEXT_CHARS else text


# ---------------------------------------------------------------------------
# Llamada a Ollama (embeddings)
# ---------------------------------------------------------------------------
def _embed_batch(texts: list[str], model: str = EMBED_MODEL) -> list[list[float]]:
    """
    Llama al endpoint /api/embed de Ollama con un lote de textos.

    La API acepta un array en 'input', lo que permite procesar
    múltiples textos en una sola llamada HTTP → mucho más eficiente
    que llamar una vez por artículo.

    Devuelve: lista de vectores, uno por texto.
    """
    payload = {
        "model": model,
        "input": texts,
    }
    resp = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # La respuesta tiene la forma: {"embeddings": [[...], [...], ...]}
    embeddings = data.get("embeddings", [])
    if len(embeddings) != len(texts):
        raise ValueError(
            f"Ollama devolvió {len(embeddings)} embeddings para {len(texts)} textos"
        )
    return embeddings


# ---------------------------------------------------------------------------
# Carga de artículos desde SQLite
# ---------------------------------------------------------------------------
def _load_articles(db_path: Path, limit: int | None = None) -> list[dict]:
    """
    Carga artículos desde SQLite.
    Incluye metadatos de article_llm_labels si existen (tier, study_type, etc.).
    """
    query = """
        SELECT
            a.canonical_id,
            a.title,
            a.abstract_text,
            a.year,
            a.journal,
            a.evidence_score,
            a.cited_by_count,
            a.url,
            COALESCE(l.study_type_llm,   a.study_type,   'unknown') AS study_type,
            COALESCE(l.evidence_tier_llm, a.evidence_tier,'unknown') AS evidence_tier,
            COALESCE(l.clinical_relevance_llm, 'unknown')            AS clinical_relevance,
            COALESCE(l.utility_score_llm, 0)                         AS utility_score
        FROM articles a
        LEFT JOIN article_llm_labels l
            ON l.canonical_id = a.canonical_id
           AND l.labeling_status = 'ollama_labeled'
        WHERE a.title IS NOT NULL
          AND a.title != ''
        ORDER BY a.evidence_score DESC, a.year DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    with sqlite3.connect(str(db_path), timeout=60) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()

    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Construcción de metadatos para ChromaDB
# ---------------------------------------------------------------------------
def _build_metadata(article: dict) -> dict:
    """
    ChromaDB solo acepta metadatos de tipo str, int o float.
    Limpiamos y convertimos todos los campos.
    """
    def _safe_str(v: Any) -> str:
        return str(v) if v is not None else ""

    def _safe_float(v: Any) -> float:
        try:
            f = float(v)
            # ChromaDB no acepta NaN ni Inf
            return f if f == f and abs(f) < 1e15 else 0.0
        except (TypeError, ValueError):
            return 0.0

    return {
        "title":              _safe_str(article["title"])[:200],
        "year":               _safe_float(article["year"]),
        "journal":            _safe_str(article["journal"])[:100],
        "evidence_score":     _safe_float(article["evidence_score"]),
        "cited_by_count":     _safe_float(article["cited_by_count"]),
        "study_type":         _safe_str(article["study_type"]),
        "evidence_tier":      _safe_str(article["evidence_tier"]),
        "clinical_relevance": _safe_str(article["clinical_relevance"]),
        "utility_score":      _safe_float(article["utility_score"]),
        "url":                _safe_str(article["url"])[:200],
    }


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def build_embeddings(
    batch_limit: int | None = None,
    dry_run: bool = False,
    model: str = EMBED_MODEL,
) -> dict:
    """
    Proceso completo de generación de embeddings.

    Returns: diccionario con estadísticas del proceso.
    """
    db_path = PROCESSED_DIR / "pcos_research.db"
    if not db_path.exists():
        print("ERROR: No se encuentra pcos_research.db")
        return {}

    # --- Cargar artículos ---
    print(f"Cargando artículos desde SQLite...")
    articles = _load_articles(db_path, limit=batch_limit)
    print(f"  {len(articles)} artículos encontrados")

    if not articles:
        print("Sin artículos para procesar.")
        return {"processed": 0, "skipped": 0, "errors": 0}

    # --- Conectar a ChromaDB ---
    if not dry_run:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            # hnsw:space=cosine → la similitud se mide por ángulo, no distancia.
            # Para texto semántico, cosine similarity es más fiable que distancia euclidiana.
        )

        # Obtener IDs ya existentes en ChromaDB para saltar los que ya están
        existing_ids = set(collection.get(include=[])["ids"])
        print(f"  {len(existing_ids)} artículos ya tienen embedding (se saltarán)")
    else:
        existing_ids = set()
        print("  [DRY RUN] No se escribirá nada.")

    # --- Filtrar artículos pendientes ---
    pending = [a for a in articles if a["canonical_id"] not in existing_ids]
    print(f"  {len(pending)} artículos pendientes de embedding\n")

    if not pending:
        print("Todo al día. No hay nada que procesar.")
        return {"processed": 0, "skipped": len(existing_ids), "errors": 0}

    # --- Procesar en lotes ---
    stats = {"processed": 0, "skipped": len(existing_ids), "errors": 0}
    t_start = time.time()

    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]

        # Construir textos
        ids    = [a["canonical_id"] for a in batch]
        texts  = [_build_text(a["title"], a["abstract_text"]) for a in batch]
        metas  = [_build_metadata(a) for a in batch]

        # Llamar a Ollama
        try:
            embeddings = _embed_batch(texts, model=model)
        except Exception as e:
            print(f"  ERROR en lote {batch_start}-{batch_start+len(batch)}: {e}")
            stats["errors"] += len(batch)
            continue

        # Guardar en ChromaDB
        if not dry_run:
            try:
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metas,
                )
            except Exception as e:
                print(f"  ERROR guardando en ChromaDB: {e}")
                stats["errors"] += len(batch)
                continue

        stats["processed"] += len(batch)

        # Progreso cada 100 artículos
        if stats["processed"] % 100 == 0 or batch_start + BATCH_SIZE >= len(pending):
            elapsed = time.time() - t_start
            rate = stats["processed"] / elapsed if elapsed > 0 else 0
            remaining = (len(pending) - stats["processed"]) / rate if rate > 0 else 0
            print(
                f"  [{stats['processed']}/{len(pending)}] "
                f"{rate:.1f} art/s | "
                f"ETA: {remaining/60:.1f} min"
            )

    # --- Resumen final ---
    total_time = time.time() - t_start
    total_in_chroma = 0
    if not dry_run:
        total_in_chroma = collection.count()

    print(f"\nCompletado en {total_time/60:.1f} minutos")
    print(f"  Procesados:  {stats['processed']}")
    print(f"  Saltados:    {stats['skipped']}  (ya tenian embedding)")
    print(f"  Errores:     {stats['errors']}")
    if not dry_run:
        print(f"  Total en ChromaDB: {total_in_chroma}")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera embeddings de artículos PCOS con nomic-embed-text y los guarda en ChromaDB"
    )
    parser.add_argument(
        "--batch", type=int, default=None,
        help="Limitar a los primeros N artículos (por defecto: todos)"
    )
    parser.add_argument(
        "--model", type=str, default=EMBED_MODEL,
        help=f"Modelo de Ollama para embeddings (default: {EMBED_MODEL})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Probar sin escribir en ChromaDB"
    )
    args = parser.parse_args()

    build_embeddings(
        batch_limit=args.batch,
        dry_run=args.dry_run,
        model=args.model,
    )
