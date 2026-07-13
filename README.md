# PCOS Research System

Sistema reproducible para investigar SOP (PCOS): literatura, ensayos clinicos y deteccion de senales estadisticas.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion

```bash
python scripts/refresh.py --days-back 60
```

Esto genera:
- `data/raw/*.jsonl`
- `data/processed/pcos_research.db`
- `data/processed/pcos_trials.pkl`
- `reports/latest_literature_brief.md`
- `reports/latest_trial_signals.md`

## Pipeline LLM (Gemini)

Backend por defecto: **Gemini API** (`gemini-2.5-flash-lite`, paid tier). Config en `.env`:
`LLM_BACKEND=gemini`, `GEMINI_API_KEY=...`, `GEMINI_MODEL=gemini-2.5-flash-lite`.

Orden: labeling → extracción → normalizer → anomaly scan. Todo automatizado con:
```bash
zsh run_pipeline.sh   # labeling -> re-extracción -> extracción -> normalizer (chunks, reanudable)
python scripts/anomaly_scan_v2.py --min-studies 2 --top-n 25   # señales cross-indication
```
O por pasos: `run_ollama_article_labeling.py` → `run_ollama_extraction.py` → `entity_normalizer.py`.
(Los scripts conservan el prefijo `run_ollama_*` por legacy; corren contra Gemini vía `llm_client.py`.)
El research agent sí usa Ollama local: `LLM_BACKEND=ollama python scripts/research_agent.py`.

## Nota
Este repositorio genera hipotesis de investigacion y no recomendaciones clinicas.
