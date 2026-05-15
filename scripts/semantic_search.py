"""
semantic_search.py
------------------
Búsqueda semántica sobre la base de conocimiento PCOS.

Dos modos de uso:
  1. RETRIEVAL puro: devuelve los N artículos más similares a una consulta.
  2. RAG (Retrieval-Augmented Generation): recupera artículos relevantes
     y se los pasa a Gemma 4 para que genere una respuesta fundamentada.

¿Qué lo hace diferente a buscar en PubMed?
  - Entiende significado, no solo palabras clave.
  - Funciona con preguntas en lenguaje natural (español o inglés).
  - Agrupa conceptos relacionados: "myo-inositol" ≈ "inositol" ≈ "D-chiro-inositol".
  - Modo RAG genera una síntesis citando artículos reales de tu base de datos.

Uso:
  # Solo recuperación (retrieval)
  python scripts/semantic_search.py "metformin insulin resistance PCOS" --top-k 5

  # RAG: recupera + genera respuesta con Gemma 4
  python scripts/semantic_search.py "que tratamientos mejoran la ovulacion en PCOS" --rag

  # Filtrar solo artículos de máxima evidencia
  python scripts/semantic_search.py "inositol ovulation" --tier tier_1 --rag

  # Buscar solo RCTs
  python scripts/semantic_search.py "lifestyle intervention weight loss" --study-type rct_or_trial
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import chromadb
import requests

# Añadir scripts/ al path para importar config
sys.path.insert(0, str(Path(__file__).parent))
from config import PROCESSED_DIR

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
OLLAMA_CHAT_URL  = "http://localhost:11434/api/chat"
EMBED_MODEL      = "nomic-embed-text"
CHAT_MODEL       = "gemma4:31b-cloud"
CHROMA_DIR       = PROCESSED_DIR / "chroma_db"
COLLECTION_NAME  = "pcos_articles"

# Número de artículos que se recuperan para pasarle al LLM en modo RAG.
# Más artículos = más contexto pero más tokens = respuesta más lenta.
RAG_CONTEXT_SIZE = 6  # articulos que pasan al LLM (menos = mas rapido, menos timeout)


# ---------------------------------------------------------------------------
# Paso 1: Embed de la consulta
# ---------------------------------------------------------------------------
def _embed_query(query: str) -> list[float]:
    """
    Convierte la consulta del usuario en un vector de 768 números.
    El mismo modelo que se usó para los artículos → mismos ejes semánticos.
    """
    resp = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "input": [query]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


# ---------------------------------------------------------------------------
# Paso 2: Búsqueda en ChromaDB
# ---------------------------------------------------------------------------
def retrieve(
    query: str,
    top_k: int = 10,
    filter_tier: str | None = None,
    filter_study_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Recupera los artículos más similares semánticamente a la consulta.

    Args:
        query:             Pregunta o términos de búsqueda (español o inglés).
        top_k:             Cuántos resultados devolver.
        filter_tier:       Filtrar por nivel de evidencia ('tier_1', 'tier_2', etc.)
        filter_study_type: Filtrar por tipo ('rct_or_trial', 'meta-analysis', etc.)

    Returns:
        Lista de dicts con metadatos + score de similitud.
    """
    # Verificar que ChromaDB existe
    if not CHROMA_DIR.exists():
        print("ERROR: No existe la base de datos vectorial.")
        print("       Ejecuta primero: python scripts/build_embeddings.py")
        return []

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        print(f"ERROR: Colección '{COLLECTION_NAME}' no encontrada.")
        return []

    n_total = collection.count()
    if n_total == 0:
        print("La base de datos vectorial está vacía. Ejecuta build_embeddings.py primero.")
        return []

    # Construir filtros de metadatos para ChromaDB
    # ChromaDB usa sintaxis: {"$and": [{"campo": {"$eq": valor}}, ...]}
    where = None
    filters = []
    if filter_tier:
        filters.append({"evidence_tier": {"$eq": filter_tier}})
    if filter_study_type:
        filters.append({"study_type": {"$eq": filter_study_type}})

    if len(filters) == 1:
        where = filters[0]
    elif len(filters) > 1:
        where = {"$and": filters}

    # Generar embedding de la consulta
    query_vector = _embed_query(query)

    # Buscar en ChromaDB
    # n_results no puede ser mayor que el total de documentos en la colección
    n_results = min(top_k, n_total)

    kwargs: dict[str, Any] = {
        "query_embeddings": [query_vector],
        "n_results": n_results,
        "include": ["metadatas", "distances", "documents"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    # Formatear resultados
    output = []
    for meta, dist, doc in zip(
        results["metadatas"][0],
        results["distances"][0],
        results["documents"][0],
    ):
        # Cosine distance → cosine similarity
        # distance=0 significa idéntico, distance=2 significa opuesto
        # similarity = 1 - distance (para cosine)
        similarity = round(1 - dist, 4)
        output.append({
            "similarity":    similarity,
            "title":         meta.get("title", ""),
            "year":          int(meta.get("year", 0)) or "???",
            "journal":       meta.get("journal", ""),
            "evidence_tier": meta.get("evidence_tier", ""),
            "study_type":    meta.get("study_type", ""),
            "utility_score": meta.get("utility_score", 0),
            "url":           meta.get("url", ""),
            "abstract_snippet": doc[:400] + "..." if len(doc) > 400 else doc,
        })

    return output


# ---------------------------------------------------------------------------
# Paso 3 (opcional): Generación con Gemma 4 (RAG)
# ---------------------------------------------------------------------------
def rag_answer(query: str, articles: list[dict]) -> str:
    """
    Genera una respuesta fundamentada usando los artículos recuperados como contexto.

    Esto es RAG (Retrieval-Augmented Generation):
      - Los artículos actúan como "memoria externa" del LLM.
      - Gemma NO inventa: solo sintetiza lo que está en los artículos.
      - Cada afirmación puede trazarse a un artículo específico.
    """
    if not articles:
        return "No hay artículos suficientes en la base de datos para responder."

    # Construir el contexto con los artículos recuperados
    context_parts = []
    for i, art in enumerate(articles[:RAG_CONTEXT_SIZE], 1):
        context_parts.append(
            f"[{i}] {art['title']} ({art['year']}) — {art['evidence_tier']}\n"
            f"    {art['abstract_snippet']}"
        )
    context = "\n\n".join(context_parts)

    # Prompt del sistema: instrucciones para Gemma
    system_prompt = """Eres un asistente de investigación médica especializado en síndrome de ovario poliquístico (PCOS/SOP).

Tu tarea es responder preguntas clínicas o científicas usando ÚNICAMENTE la evidencia proporcionada en el contexto.

Reglas estrictas:
1. Solo afirma lo que está respaldado por los artículos del contexto.
2. Cita el número de artículo entre corchetes [1], [2], etc.
3. Indica el nivel de evidencia cuando sea relevante (tier_1 = más fuerte).
4. Si los artículos no responden la pregunta directamente, dilo claramente.
5. No inventes datos, dosis, estadísticas ni conclusiones.
6. Responde en español, terminología técnica en inglés cuando corresponda.
7. Sé conciso: máximo 300 palabras."""

    # Prompt del usuario con contexto
    user_prompt = f"""Pregunta: {query}

Artículos de la base de datos:
{context}

Responde basándote solo en los artículos anteriores."""

    # Llamar a Gemma 4 vía Ollama
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0},  # temperatura 0 = determinista, sin invención
    }

    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ---------------------------------------------------------------------------
# Función principal: combina retrieval + RAG opcional
# ---------------------------------------------------------------------------
def search(
    query: str,
    top_k: int = 5,
    use_rag: bool = False,
    filter_tier: str | None = None,
    filter_study_type: str | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Búsqueda semántica completa.

    Returns dict con:
      - 'articles': lista de artículos recuperados (ordenados por similitud)
      - 'answer':   respuesta generada por Gemma (si use_rag=True)
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"  Query: \"{query}\"")
        filters_desc = []
        if filter_tier:       filters_desc.append(f"tier={filter_tier}")
        if filter_study_type: filters_desc.append(f"type={filter_study_type}")
        if filters_desc: print(f"  Filtros: {', '.join(filters_desc)}")
        print(f"{'='*60}\n")

    # Paso 1+2: Embed + Retrieve
    articles = retrieve(query, top_k=top_k, filter_tier=filter_tier, filter_study_type=filter_study_type)

    if verbose and articles:
        print(f"Top {len(articles)} artículos más relevantes:\n")
        for i, art in enumerate(articles, 1):
            tier_badge = {"tier_1": "[T1]", "tier_2": "[T2]", "tier_3": "[T3]", "tier_4": "[T4]"}.get(art['evidence_tier'], "[??]")
            print(f"  {i}. sim={art['similarity']:.3f} {tier_badge} [{art['year']}]")
            print(f"     {art['title'][:80]}")
            print(f"     {art['study_type']} | {art['journal'][:50]}")
            if art['url']:
                print(f"     {art['url']}")
            print()

    # Paso 3 (opcional): RAG
    answer = None
    if use_rag and articles:
        if verbose:
            print('-'*60)
            print("  Generando respuesta con Gemma 4...\n")
        answer = rag_answer(query, articles)
        if verbose:
            print(f"RESPUESTA:\n{answer}\n")

    return {"articles": articles, "answer": answer}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Búsqueda semántica en la base de conocimiento PCOS"
    )
    parser.add_argument(
        "query",
        help="Pregunta o términos de búsqueda (español o inglés)"
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Número de artículos a recuperar (default: 5)"
    )
    parser.add_argument(
        "--rag", action="store_true",
        help="Activar modo RAG: genera respuesta con Gemma 4 usando los artículos como contexto"
    )
    parser.add_argument(
        "--tier",
        choices=["tier_1", "tier_2", "tier_3", "tier_4"],
        default=None,
        help="Filtrar por nivel de evidencia"
    )
    parser.add_argument(
        "--study-type",
        choices=["guideline", "meta-analysis", "rct_or_trial", "cohort", "review", "other"],
        default=None,
        help="Filtrar por tipo de estudio"
    )
    parser.add_argument(
        "--model", type=str, default=CHAT_MODEL,
        help=f"Modelo LLM para RAG (default: {CHAT_MODEL})"
    )

    args = parser.parse_args()
    CHAT_MODEL = args.model

    search(
        query=args.query,
        top_k=args.top_k,
        use_rag=args.rag,
        filter_tier=args.tier,
        filter_study_type=args.study_type,
    )
