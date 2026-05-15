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

## Extraccion local con Ollama

1. Instala Ollama y arranca el servicio local.
2. Descarga un modelo, por ejemplo:
```bash
ollama pull qwen2.5:7b-instruct
```
3. Ejecuta el runner local:
```bash
python scripts/run_ollama_extraction.py --top-k 10 --model qwen2.5:7b-instruct
```
4. Si quieres probar solo el flujo sin llamar al modelo:
```bash
python scripts/run_ollama_extraction.py --top-k 10 --dry-run
```

La salida se guarda en la tabla `article_extractions` y en `data/processed/ollama_article_extractions.jsonl`.

## Nota
Este repositorio genera hipotesis de investigacion y no recomendaciones clinicas.
