# Data Quality Report

- Articulos crudos tras filtro de relevancia: 13397
- Articulos deduplicados: 12155
- Duplicados fusionados: 1242
- Ensayos normalizados: 1133
- Articulos listos para LLM: 12155
- Articulos con abstract: 6958
- Articulos sin año válido (filtrados): 5057
- Version de esquema LLM: 1.0

## Nota

- study_type y evidence_tier no se infieren por heurística.
- Se asignan mediante LLM (tabla article_llm_labels).
- evidence_score se basa en: citaciones + completitud de metadatos + recencia.
