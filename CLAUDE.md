# Sistema de Investigacion SOP (PCOS) - Protocolo Operativo

## Objetivo
Construir y mantener un sistema reproducible para investigar el sindrome de ovario poliquistico (SOP/PCOS), con tres capas:
1. Base de conocimiento robusta (guias + revisiones + ensayos clave).
2. Vigilancia de evidencia reciente (experimental/traslacional y clinica).
3. Deteccion de senales estadisticas de beneficio inesperado en tratamientos (incluyendo tratamientos no concebidos inicialmente para SOP).

## Backend LLM (actual)
Pipeline (labeling + extraccion v1.3 + normalizer) corre contra **Gemini API** `gemini-2.5-flash-lite` (paid tier) via `llm_client.py`. `.env`: `LLM_BACKEND=gemini`, `GEMINI_MODEL=gemini-2.5-flash-lite`. `thinking` desactivado (JSON fiable). Research agent: Ollama local `gemma4:12b`. Embeddings: Ollama `nomic-embed-text`. (Scripts `run_ollama_*` son nombre legacy; ya usan Gemini.)

## Estado actual (medido en BD, 2026-07-12)
- articles **12,155** · trials **1,133** · fulltexts **4,300** (pmc 4,150 · s2 132 · abstract 18; europe_pmc 0)
- labeling **12,155** (100%) · extracciones **7,012** (v1.3: 6,896 · v1.0: 116)
- effect_direction: **unclear 82%** · favorable 762 · mixed 292 · neutral 137 · unfavorable 69
- entidades **1,995** · entity_links **6,254** · mechanism_links (KG) **23,451** · señales **1,309**
- gold_labels **115** (solo clasificación; effect/intervention/n_total sin validar)
- Prioridad TOP acordada: expandir + de-truncar full text (Results capado a 2000 chars).

## Estructura del sistema
- `scripts/fetch_pubmed.py` / `fetch_openalex.py` / `fetch_clinicaltrials.py`: ingesta (PubMed, OpenAlex, ClinicalTrials.gov).
- `scripts/run_ollama_article_labeling.py` → `run_ollama_extraction.py` → `entity_normalizer.py`: pipeline LLM (labeling, extraccion con mechanisms, normalizacion de entidades).
- `run_pipeline.sh`: orquestador del pipeline LLM (chunks de 500, reanudable).
- `scripts/anomaly_scan_v2.py`: barrido estadistico y deteccion de senales (detectores T1-T9).
- `scripts/research_agent.py`: deep-dive ReAct (Ollama local).
- `scripts/refresh.py`: orquestador de ingesta (fetch) completa.
- `data/raw/`: ingesta cruda JSONL.
- `data/processed/`: tablas limpias, `pcos_research.db`, `pcos_trials.pkl`.
- `reports/`: resumenes ejecutivos y hallazgos.

## Regla de calidad de evidencia
- Incluir primero:
  - Guias internacionales y consensos metodologicamente fuertes.
  - Revisiones sistematicas / meta-analisis de RCT.
  - RCT multicentricos y estudios clinicos con resultados reproducibles.
- Bajar prioridad a:
  - Series pequenas no controladas.
  - Editoriales u opiniones sin datos primarios.
  - Preprints sin revision por pares (solo como vigilancia).

### Ranking interno (evidence_tier)
- `tier_1`: guia internacional, meta-analisis RCT, RCT robusto.
- `tier_2`: cohorte prospectiva, RCT pequeno, estudio mecanistico con componente humano.
- `tier_3`: retrospectivo pequeno, piloto sin control fuerte.
- `tier_4`: narrativa/opinion/hypothesis sin validacion clinica.

## Campos minimos por articulo
- `source_id` (PMID/DOI/OpenAlex ID)
- `title`
- `year`
- `journal`
- `study_type` (guia, meta-analisis, RCT, cohorte, etc.)
- `population`
- `n_total`
- `intervention`
- `comparator`
- `main_outcomes`
- `effect_direction` (favorable, neutral, desfavorable, mixto)
- `limitations`
- `evidence_tier`
- `summary_short` (120-220 palabras)
- `url`

## Campos minimos por estudio clinico
- `nct_id`
- `status`
- `phase`
- `conditions`
- `interventions`
- `enrollment`
- `sex`
- `age`
- `outcome_measures`
- `has_results`
- `results_first_posted`
- `completion_date`
- `linked_publications`
- `url`

## Deteccion de anomalias estadisticas (tratamientos)
Definicion operativa de "senal":
1. Intervencion con efecto favorable en >=2 estudios independientes.
2. Al menos un endpoint clinico relevante para SOP (ciclo menstrual, ovulacion, hiperandrogenismo, HOMA-IR, BMI, fertilidad, calidad de vida).
3. Consistencia de direccion de efecto > 60%.
4. Penalizacion por tamano muestral pequeno y alto riesgo de sesgo.

El `anomaly_scan_v2.py` calcula:
- frecuencia de beneficio por intervencion,
- score de consistencia,
- score ponderado por tamano muestral,
- "cross-indication signal" (farmaco de otra indicacion con beneficio potencial en SOP).

## Fuentes y APIs oficiales
- PubMed E-utilities (NCBI)
- ClinicalTrials.gov API v2
- OpenAlex API (descubrimiento y citaciones)

## Politica de privacidad y limites
- No recolectar datos personales identificables.
- El sistema trabaja con datos publicados, anonimizados o agregados.
- Historiales medicos individuales completos suelen requerir acuerdos de acceso (p. ej. repositorios controlados).
- Separar claramente "senal exploratoria" de "recomendacion clinica".

## Flujo de refresh (cuando el usuario diga "refresh")
Ejecutar en este orden:
1. `python scripts/refresh.py --days-back 60`
2. Revisar `reports/latest_literature_brief.md`
3. Revisar `reports/latest_trial_signals.md`
4. Comparar nuevas senales con baseline historico (`data/processed/pcos_research.db`)
5. Actualizar `reports/priority_hypotheses.md` con:
   - hipotesis mecanistica,
   - plausibilidad clinica,
   - riesgo/beneficio,
   - nivel de evidencia actual.

## Estandar de resumen de articulos
Cada articulo prestigioso y revisado por pares debe tener:
- Contexto (1 frase)
- Metodo (1-2 frases)
- Resultado principal (1-2 frases con magnitud si existe)
- Limitaciones (1 frase)
- Valor para SOP (1 frase critica)

Longitud objetivo: 120-220 palabras por articulo.

## Criterios de "articulo prestigioso"
- Revista de alto impacto en endocrinologia, ginecologia, medicina interna o fertilidad.
- Revision por pares y trazabilidad (PMID/DOI).
- Metodologia reportada con claridad.
- Relevancia directa o mecanistica fuerte para SOP.

## Comandos rapidos
- Primera carga:
  - `python scripts/refresh.py --days-back 3650`
- Actualizacion periodica:
  - `python scripts/refresh.py --days-back 60`
- Solo literatura:
  - `python scripts/fetch_pubmed.py --days-back 60`
- Solo ensayos:
  - `python scripts/fetch_clinicaltrials.py --query "polycystic ovary syndrome"`
- Barrido de senales:
  - `python scripts/anomaly_scan_v2.py --min-studies 2 --top-n 25`

## Entregables esperados tras cada refresh
- `reports/latest_literature_brief.md`
- `reports/latest_trial_signals.md`
- `reports/priority_hypotheses.md`
- `data/processed/pcos_research.db`
- `data/processed/pcos_trials.pkl`

## Nota importante
Este sistema es de investigacion y generacion de hipotesis; no sustituye criterio medico ni guias clinicas.
