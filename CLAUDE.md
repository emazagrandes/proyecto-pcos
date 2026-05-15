# Sistema de Investigacion SOP (PCOS) - Protocolo Operativo

## Objetivo
Construir y mantener un sistema reproducible para investigar el sindrome de ovario poliquistico (SOP/PCOS), con tres capas:
1. Base de conocimiento robusta (guias + revisiones + ensayos clave).
2. Vigilancia de evidencia reciente (experimental/traslacional y clinica).
3. Deteccion de senales estadisticas de beneficio inesperado en tratamientos (incluyendo tratamientos no concebidos inicialmente para SOP).

## Estructura del sistema
- `scripts/fetch_pubmed.py`: literatura cientifica desde PubMed (E-utilities).
- `scripts/fetch_openalex.py`: metadatos ampliados/citaciones y descubrimiento semantico.
- `scripts/fetch_clinicaltrials.py`: ensayos clinicos desde ClinicalTrials.gov API v2.
- `scripts/build_knowledge_base.py`: normalizacion, scoring de evidencia y resumen conciso.
- `scripts/anomaly_scan.py`: barrido estadistico y deteccion de anomalias.
- `scripts/refresh.py`: orquestador de actualizacion completa.
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

El `anomaly_scan.py` calcula:
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
  - `python scripts/anomaly_scan.py`

## Entregables esperados tras cada refresh
- `reports/latest_literature_brief.md`
- `reports/latest_trial_signals.md`
- `reports/priority_hypotheses.md`
- `data/processed/pcos_research.db`
- `data/processed/pcos_trials.pkl`

## Nota importante
Este sistema es de investigacion y generacion de hipotesis; no sustituye criterio medico ni guias clinicas.
