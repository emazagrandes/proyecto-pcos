# Ollama Labeling Report

- Model: gemini-2.5-flash-lite
- Dry run: False
- Prompt version: article-label-v2-guided
- Registros procesados: 15

## Distribucion

### study_type_llm
- cohort: 5
- other: 3
- rct_or_trial: 3
- preclinical: 2
- meta-analysis: 1
- review: 1

### evidence_tier_llm
- tier_3: 6
- tier_4: 4
- tier_1: 4
- tier_2: 1

### clinical_relevance_llm
- medium: 8
- high: 5
- low: 2

## Ejemplos

### 10.15171/apb.2017.078
- study_type_llm: preclinical
- evidence_tier_llm: tier_4
- clinical_relevance_llm: low
- utility_score_llm: 45.0
- llm_label_reasoning: Animal model, potential mechanistic insights into spearmint effects on PCOS.

### 10.5468/ogs.2016.59.5.367
- study_type_llm: meta-analysis
- evidence_tier_llm: tier_1
- clinical_relevance_llm: high
- utility_score_llm: 85.0
- llm_label_reasoning: Meta-analysis of human studies on PCOS and breast cancer association.

### 10.5812/ijem.17954
- study_type_llm: cohort
- evidence_tier_llm: tier_3
- clinical_relevance_llm: medium
- utility_score_llm: 65.0
- llm_label_reasoning: Case-control study, human data, relevant to PCOS comorbidities.

### 10.5812/ircmj.12423
- study_type_llm: other
- evidence_tier_llm: tier_4
- clinical_relevance_llm: low
- utility_score_llm: 20.0
- llm_label_reasoning: Qualitative study, not directly clinical or mechanistic for PCOS.

### comparison of free androgen index in polycystic ovary syndrome and non polycystic ovary syndrome infertile patients
- study_type_llm: cohort
- evidence_tier_llm: tier_3
- clinical_relevance_llm: medium
- utility_score_llm: 65.0
- llm_label_reasoning: Cross-sectional study comparing hormonal profiles in PCOS vs. infertile controls.

