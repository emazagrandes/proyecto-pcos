# Gold Label Progress

## Estado actual
- Filas con propuesta cargada en `article_gold_labels`: 15
- Estado `codex_high_confidence`: 7
- Estado `proposed_by_codex`: 8
- CSV base de revision: `data/processed/gold_label_candidates.csv`
- CSV con propuestas: `data/processed/gold_label_candidates_with_suggestions.csv`
- CSV sembrado para comparacion: `data/processed/gold_label_seeded.csv`

## Que significa cada estado
- `codex_high_confidence`: propuesta bastante solida, aun pendiente de validacion humana final.
- `proposed_by_codex`: propuesta razonable pero mas ambigua o debatible.

## Siguiente uso recomendado
1. Validar primero los 7 casos `codex_high_confidence`.
2. Revisar despues los 8 casos ambiguos con mas cuidado.
3. Crear una futura categoria `reviewed_human` cuando esten confirmados.
4. Usar ese subconjunto como base de evaluacion de heuristica y LLM.

## Casos ejemplo ya sembrados
- `10.1093/humupd/dmae028` -> `meta-analysis / tier_1`
- `10.1186/s12958-025-01372-5` -> `guideline / tier_1`
- `10.1111/cen.70000` -> `cohort / tier_2`
- `10.1007/s12020-024-04121-7` -> `other / tier_4`
- `10.1016/j.jclinepi.2025.111789` -> `other / tier_4`
