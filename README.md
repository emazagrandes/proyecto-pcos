# PCOS Research System

A data pipeline that ingests scientific literature on polycystic ovary syndrome (PCOS), extracts structured clinical data with LLMs, and runs statistical signal detection to surface potential drug repurposing candidates — interventions studied in other conditions that show consistent favorable effects in PCOS.

## Scale

- **12,155 articles** (PubMed + OpenAlex) · **1,133 clinical trials** (ClinicalTrials.gov)
- **4,300 full texts** fetched (PMC XML, Semantic Scholar)
- **6,893 structured extractions** (intervention, population, effect direction, mechanisms)
- **23,451 knowledge graph triples** (mechanism_links)
- **1,995 canonical entities** · **1,309 intervention signals**

## Architecture

Five layers:

1. **Ingestion** — PubMed E-utilities, OpenAlex, ClinicalTrials.gov v2
2. **Knowledge base** — SQLite + ChromaDB embeddings
3. **LLM processing** — evidence tiering → structured extraction (schema v1.3) → entity normalization (4-layer: seed, exact, fuzzy, LLM-verify)
4. **Knowledge graph** — mechanism triples + multi-hop BFS traversal (`graph_query.py`)
5. **Signal detection** — `anomaly_scan_v2.py` (9 detector types) + `research_agent.py` (ReAct loop, 8 tools)

## Running

```bash
pip install -r requirements.txt
cp .env.example .env  # add GEMINI_API_KEY

# Full ingestion
python scripts/refresh.py --days-back 60

# LLM pipeline (labeling → extraction → normalization)
zsh run_pipeline.sh

# Signal detection
python scripts/anomaly_scan_v2.py --min-studies 2 --top-n 25

# Research agent (deep-dive on a signal)
LLM_BACKEND=ollama python scripts/research_agent.py --from-scan --top-k 3
```

## LLM backend

Gemini API (`gemini-2.5-flash-lite`) for batch processing. Ollama local (`gemma4:12b`) for the research agent. Backend is swappable via `LLM_BACKEND` env var — `llm_client.py` abstracts both.

## Disclaimer

This system generates exploratory research hypotheses. It does not provide clinical recommendations.
