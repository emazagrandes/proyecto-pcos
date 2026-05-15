# Label Evaluation

- Articulos evaluados: 15
- Heuristica study_type vs gold: 33.3%
- LLM study_type vs gold: 100.0%
- Heuristica evidence_tier vs gold: 40.0%
- LLM evidence_tier vs gold: 100.0%
- Cobertura LLM clinical_relevance: 26.7%
- Cobertura LLM utility_score: 26.7%

## Ganadores por campo

- study_type: {'tie': 6, 'heuristic': 5, 'llm': 4}
- evidence_tier: {'heuristic': 6, 'tie': 5, 'llm': 4}

## Ejemplos

### 10.1093/humupd/dmae028
- gold: meta-analysis / tier_1
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: tie
- winner_tier: heuristic
- review_status: codex_high_confidence

### 10.1186/s12958-025-01372-5
- gold: guideline / tier_1
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: heuristic
- winner_tier: heuristic
- review_status: codex_high_confidence

### 10.1016/j.bpobgyn.2026.102702
- gold: review / tier_2
- heuristica: guideline / tier_1
- llm: review / tier_2
- winner_study_type: llm
- winner_tier: llm
- review_status: proposed_by_codex

### 10.5468/ogs.24288
- gold: guideline / tier_1
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: heuristic
- winner_tier: heuristic
- review_status: codex_high_confidence

### 10.1080/09513590.2025.2456578
- gold: guideline / tier_1
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: heuristic
- winner_tier: heuristic
- review_status: proposed_by_codex

### 10.1111/obr.70072
- gold: review / tier_2
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: tie
- winner_tier: tie
- review_status: proposed_by_codex

### 10.1111/aogs.14725
- gold: review / tier_2
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: tie
- winner_tier: tie
- review_status: proposed_by_codex

### 10.1093/humrep/deae042
- gold: cohort / tier_2
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: tie
- winner_tier: tie
- review_status: codex_high_confidence

### 10.1111/cen.70000
- gold: cohort / tier_2
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: tie
- winner_tier: tie
- review_status: codex_high_confidence

### 10.1016/j.eclinm.2024.102927
- gold: guideline / tier_1
- heuristica: guideline / tier_1
- llm: None / None
- winner_study_type: heuristic
- winner_tier: heuristic
- review_status: proposed_by_codex

