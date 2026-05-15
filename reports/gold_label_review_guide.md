# Gold Label Review Guide

## Objetivo
Convertir articulos complejos en etiquetas fiables para futura evaluacion y fine-tuning.

## Orden de lectura
1. Lee el titulo.
2. Lee el abstract buscando primero METHODS y RESULTS.
3. Decide el `study_type` real.
4. Asigna `evidence_tier` segun el diseno, no segun el prestigio de la revista.
5. Valora `clinical_relevance` y `mechanistic_relevance` por separado.
6. Da un `utility_score` de 0 a 100.
7. Escribe una nota corta en `review_notes` explicando la decision.

## Como decidir study_type
- `guideline`: guia formal, consenso Delphi, practice recommendation, resumen ejecutivo de guia.
- `meta-analysis`: revision sistematica con pooling cuantitativo o diagnostic meta-analysis.
- `review`: revision narrativa o resumen de guias sin cohorte ni trial originales.
- `rct_or_trial`: ensayo clinico o estudio intervencional.
- `cohort`: observacional, retrospectivo, prospectivo, cross-sectional o survey con muestra humana.
- `protocol`: protocolo sin resultados.
- `preclinical`: animal, in vitro, celular, no humano.
- `case_report`: uno o muy pocos pacientes, anecdotal.
- `other`: metodologia, vigilancia bibliografica, evaluacion de LLMs, editorial, comentario.

## Como decidir evidence_tier
- `tier_1`: guideline/consensus formal, meta-analysis fuerte, RCT robusto.
- `tier_2`: cohorte buena o estudio humano mecanistico fuerte.
- `tier_3`: retrospectivo pequeno, cross-sectional, survey-heavy, observacional con aplicabilidad limitada.
- `tier_4`: metodologia, opinion, editorial, hypothesis paper, case report.

## Clinical vs mechanistic relevance
- `clinical_relevance = high` si ayuda directamente a diagnostico, tratamiento, infertilidad, seguimiento o outcomes clinicos en PCOS.
- `mechanistic_relevance = high` si ilumina biomarcadores, fisiopatologia, vias hormonales o metabolicas con valor explicativo.
- No mezclar ambas: un paper metodologico puede mencionar PCOS y aun asi tener relevancia clinica baja.

## Utility score orientativo
- 90-100: pieza de referencia clara para decision o sintesis mayor.
- 75-89: util e informativo, pero con limites de diseno o alcance.
- 50-74: aporta contexto, subgrupo o metodologia util.
- 0-49: utilidad baja para construir conocimiento clinico central.

## Regla practica
Si el paper trata sobre una guia, eso no lo convierte automaticamente en `guideline`.
Pregunta correcta: `este paper ES una guia/consenso o ESTUDIA una guia?`
