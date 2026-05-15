# Gold Dataset Expansion

## Estado nuevo
- Total en `article_gold_labels`: 115
- `codex_high_confidence`: 7
- `proposed_by_codex`: 18
- `pending_review`: 90
- Batch ampliado generado: `data/processed/gold_label_batch_100.csv`
- Ejemplos nuevos sembrados: `data/processed/gold_label_batch_seeded_examples.csv`

## Por que estos 10 nuevos son buenos ejemplos
Se eligieron porque son casos relativamente claros y variados:
- meta-analysis terapeuticos
- meta-analysis diagnosticos
- RCTs directos en PCOS
- un caso `other` importante (`Expression of Concern`)
- revisiones sistematicas sin pooling claramente expreso

## Ejemplos sembrados
- `10.1097/ms9.0000000000004506` -> `meta-analysis / tier_1`
- `10.1186/s12905-025-04201-4` -> `meta-analysis / tier_1`
- `10.4103/aam.aam_306_24` -> `meta-analysis / tier_1`
- `10.1001/jama.2025.13668` -> `rct_or_trial / tier_1`
- `10.1186/s12958-025-01447-3` -> `rct_or_trial / tier_1`
- `10.1007/s10815-025-03500-x` -> `rct_or_trial / tier_1`
- `10.1016/j.metop.2024.100343` -> `meta-analysis / tier_1`
- `10.1016/j.jpag.2026.01.001` -> `review / tier_2`
- `10.3390/nu17020310` -> `review / tier_2`
- `10.3892/etm.2025.13024` -> `other / tier_4`
