"""
llm_support.py
==============
Prompt engineering for PCOS evidence extraction with Gemma 4.

Architecture:
- SYSTEM_PROMPT:      Role + principles. Goes in the "system" turn.
- EXTRACTION_FIELDS:  Field-by-field instructions for the user prompt.
- FEW_SHOT_EXAMPLES:  2 complete examples (RCT + mechanistic/animal).
                      The single biggest quality improvement for LLMs.
- build_extraction_prompt(row):  Canonical prompt builder used by
                      run_ollama_extraction.py.

Schema version: 1.2
"""

import json
from typing import Any

EXTRACTION_SCHEMA_VERSION = "1.3"

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# Given to Gemma as the "system" turn — sets role, goal, and key principles.
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert biomedical research analyst specializing in PCOS \
(polycystic ovary syndrome) clinical and translational research.

Your task is to read a research record and extract structured evidence \
into precise JSON. This data feeds an automated anomaly-detection system \
that looks for unexpected treatment signals across thousands of papers — \
so accuracy and granularity matter more than speed.

Core principles:
1. NULL > wrong value. When a field is genuinely not inferable from the text, \
use null. Do not invent or hallucinate.
2. effect_direction must reflect the CLINICAL outcome for PCOS patients, \
not just whether p < 0.05.
3. population sub-fields (bmi, ethnicity, diet, comorbidities) are critical \
for detecting differential effects across patient subgroups. Extract them \
even when they require inference from study location or BMI mean values.
4. intervention should be the specific treatment being tested — not the \
disease, not the study design.
5. Mechanistic, animal, and in vitro studies → effect_direction = "unclear" \
unless the paper reports direct clinical outcomes in humans.
"""

# ─────────────────────────────────────────────────────────────────────────────
# FIELD GUIDANCE
# Per-field instructions. More specific = better fill rate.
# ─────────────────────────────────────────────────────────────────────────────

EXTRACTION_FIELDS: dict[str, str] = {

    "population": (
        "One sentence describing the study population. "
        "Include: condition (PCOS), n, weight/BMI, age, country if mentioned. "
        "Example: '60 lean Iranian women with PCOS aged 18-40'."
    ),

    "population_diet": (
        "Dietary pattern of the study population, if explicitly mentioned. "
        "Examples: 'low-calorie diet', 'Mediterranean diet', 'ketogenic', "
        "'standard diet', 'high-fat Western diet'. "
        "Use null if diet is not described — do NOT infer 'standard diet' by default."
    ),

    "population_bmi": (
        "BMI category or mean BMI of participants. "
        "Inference rules:\n"
        "  - Explicit BMI value: mean BMI 32 → 'obese (mean BMI 32)'\n"
        "  - BMI < 25 or descriptors 'lean', 'normal-weight', 'non-obese' → 'lean/normal-weight'\n"
        "  - BMI 25–29.9 or 'overweight' → 'overweight'\n"
        "  - BMI ≥ 30 or 'obese' → 'obese'\n"
        "  - Selection criteria 'BMI > 25' → 'overweight/obese'\n"
        "  - Mixed or wide range → 'mixed BMI'\n"
        "  - Not reported and not inferable → null"
    ),

    "population_age_range": (
        "Age range or mean age as a string. "
        "Examples: '18-35 years', 'mean 27.4 ± 4.1 years', 'reproductive age (18-45)', "
        "'adolescents (13-18)'. "
        "Use null if not reported."
    ),

    "population_comorbidities": (
        "List of comorbidities or specific metabolic features that characterize "
        "the population (NOT the PCOS diagnosis itself). "
        "Examples: ['insulin resistance'], ['obesity', 'anovulatory infertility'], "
        "['type 2 diabetes'], ['hypothyroidism']. "
        "Do NOT include 'PCOS' itself — that is the primary condition, not a comorbidity. "
        "Use [] if none are mentioned."
    ),

    "population_ethnicity": (
        "Ethnicity or region of recruitment of the study population. "
        "Inference rules:\n"
        "  - Explicit statement always takes priority\n"
        "  - Infer from study location: Iran → 'Iranian', China → 'Chinese', "
        "India → 'Indian', Italy → 'Italian', Turkey → 'Turkish', "
        "Egypt → 'Egyptian', Korea → 'Korean', Saudi Arabia → 'Saudi'\n"
        "  - Multi-country or Western multicenter → 'mixed/international'\n"
        "  - Not inferable → null"
    ),

    "n_total": (
        "Total number of participants enrolled (integer). "
        "Use the enrollment number, not the number who completed. "
        "Use null if not stated."
    ),

    "intervention": (
        "The specific treatment, drug, supplement, or procedure being evaluated. "
        "Use the canonical name — not trade names, not abbreviations if the full name is given. "
        "Examples: 'metformin 1500mg/day', 'resveratrol supplementation', "
        "'laparoscopic ovarian drilling', 'low-calorie diet'. "
        "Do NOT include the comparator here."
    ),

    "comparator": (
        "The control, placebo, or reference treatment being compared to the intervention. "
        "Examples: 'placebo', 'metformin alone', 'no treatment', 'standard care'. "
        "Use null if there is no comparator (single-arm or observational study)."
    ),

    "main_outcomes": (
        "List of the specific clinical or biochemical outcomes measured. "
        "Use precise names, not vague categories. "
        "Good: ['HOMA-IR', 'total testosterone', 'menstrual cycle regularity', 'ovulation rate']. "
        "Bad: ['metabolic parameters', 'hormonal profile', 'reproductive outcomes']. "
        "Include 3-6 of the most important outcomes."
    ),

    "effect_direction": (
        "The overall clinical effect of the intervention on PCOS-relevant outcomes:\n"
        "  'favorable'   — primary outcomes significantly improved in the desired direction "
        "(e.g., testosterone reduced, HOMA-IR improved, cycles regularized, ovulation restored)\n"
        "  'unfavorable' — primary outcomes significantly worsened\n"
        "  'neutral'     — no statistically significant difference between groups\n"
        "  'mixed'       — some outcomes improved but primary endpoint not met, "
        "OR conflicting results (some better, some worse, some unchanged)\n"
        "  'unclear'     — mechanistic study, animal study, in vitro only, "
        "OR insufficient data to make a clinical judgment\n"
        "Note: animal/in vitro/mechanistic studies → always 'unclear', even if results are positive."
    ),

    "limitations": (
        "List 2-4 specific methodological limitations. "
        "Be precise — avoid generic phrases like 'more research needed'. "
        "Good: ['small sample size (n=30)', 'no placebo control', 'short follow-up (8 weeks)', "
        "'single-center study', 'self-reported outcomes']. "
        "Use [] if the paper does not state limitations."
    ),

    "reasoning_summary": (
        "2-3 sentence explanation of HOW you inferred the key fields, especially "
        "effect_direction and any population fields you inferred rather than read directly. "
        "This is used for quality control — be honest about uncertainty."
    ),

    "notable_finding": (
        "OPTIONAL. Fill this ONLY if the study contains something genuinely surprising, "
        "unexpected, or anomaly-worthy that a PCOS researcher should not miss. "
        "Leave null for ordinary results.\n"
        "Situations that warrant filling this field:\n"
        "  - A drug or supplement not typically used for PCOS showing unusually large benefit "
        "(e.g., an antidepressant, an antibiotic, a cancer drug)\n"
        "  - Effect size dramatically larger than what the literature usually reports "
        "(e.g., testosterone reduced by >50%)\n"
        "  - A finding that directly contradicts current clinical guidelines or consensus\n"
        "  - A striking subpopulation effect (e.g., intervention works only in lean PCOS, "
        "or has opposite effect in insulin-resistant vs. non-IR patients)\n"
        "  - An unexpected co-benefit or harm (e.g., fertility drug also reversed metabolic syndrome)\n"
        "  - A mechanistic finding that opens a completely new hypothesis\n"
        "Format: 1-2 sentences, specific and factual. No vague praise like 'interesting results'.\n"
        "Good example: 'Surprisingly, low-dose naltrexone reduced AMH by 38% (p<0.001) in lean PCOS, "
        "an effect never previously reported for this drug class.'\n"
        "Bad example: 'This study found interesting results that may be relevant to PCOS.'"
    ),

    "mechanisms": (
        "OPTIONAL. List of causal/mechanistic relationships mentioned or implied in this study. "
        "Each item is a triple: source → relation → target.\n"
        "Relation types allowed (use exactly these strings):\n"
        "  'activates'       — source activates/upregulates/stimulates target\n"
        "  'inhibits'        — source inhibits/blocks/suppresses/downregulates target\n"
        "  'improves'        — source has favorable clinical effect on target\n"
        "  'reduces'         — source reduces/decreases target (quantitative)\n"
        "  'increases'       — source increases/elevates target (quantitative)\n"
        "  'associated_with' — epidemiological or correlational link\n"
        "  'indicates'       — target is a biomarker/diagnostic indicator of source\n"
        "  'tested_in'       — intervention was tested in this condition/population\n"
        "Node types for source/target:\n"
        "  interventions: drugs, supplements, procedures, diets\n"
        "  mechanisms: molecular pathways, receptors, enzymes (e.g., 'NF-kB', 'AMPK')\n"
        "  biomarkers: measurable molecules (e.g., 'TNF-alpha', 'testosterone', 'HOMA-IR')\n"
        "  outcomes: clinical results (e.g., 'ovulation rate', 'menstrual regularity')\n"
        "  comorbidities: diseases (e.g., 'insulin resistance', 'type 2 diabetes')\n"
        "Rules:\n"
        "  - Use canonical lowercase names (e.g., 'NF-kB' not 'nuclear factor kappa B')\n"
        "  - Extract 2-6 triples maximum — quality over quantity\n"
        "  - Only include relationships explicitly stated or directly implied by the study\n"
        "  - Use [] if no clear mechanistic relationships are described\n"
        "Format: [{\"source\": \"X\", \"relation\": \"inhibits\", \"target\": \"Y\", "
        "\"confidence\": 0.9}, ...]\n"
        "confidence: 0.9=explicitly stated with data, 0.7=stated without data, "
        "0.5=implied/inferred"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES
# Two complete demonstrations. This is the single biggest quality improvement.
# Example 1: RCT with clear favorable outcome
# Example 2: Study with mixed/unclear result to calibrate effect_direction
# ─────────────────────────────────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = """
## Example 1 — Randomized controlled trial, favorable result

Source:
Title: Resveratrol supplementation and hormonal and metabolic profiles in women with PCOS
Journal: Journal of Clinical Endocrinology & Metabolism
Year: 2018
Study type: RCT
Abstract: In this double-blind placebo-controlled trial, 60 lean women with PCOS (BMI 19–24 kg/m²,
aged 18–40) in Tehran were randomized to resveratrol 1500 mg/day or placebo for 3 months.
Resveratrol significantly reduced total testosterone (−28%, p=0.001), DHEAS (p=0.01), and HOMA-IR
(p=0.03). Menstrual regularity improved in 67% of the resveratrol group vs 28% placebo (p=0.004).
Limitations: single-center, short duration, Iranian population only.

Output:
{
  "schema_version": "1.2",
  "population": "60 lean Iranian women with PCOS, aged 18-40",
  "population_diet": null,
  "population_bmi": "lean/normal-weight (BMI 19-24)",
  "population_age_range": "18-40 years",
  "population_comorbidities": [],
  "population_ethnicity": "Iranian",
  "n_total": 60,
  "intervention": "resveratrol 1500mg/day",
  "comparator": "placebo",
  "main_outcomes": ["total testosterone", "DHEAS", "HOMA-IR", "menstrual regularity"],
  "effect_direction": "favorable",
  "limitations": ["single-center", "short duration (3 months)", "Iranian population only"],
  "reasoning_summary": "RCT with placebo control. All key PCOS endpoints (androgens, insulin resistance, menstrual regularity) improved significantly. effect_direction=favorable because primary outcomes moved in clinically desired direction. BMI inferred from reported range 19-24. Ethnicity inferred from Tehran study location.",
  "notable_finding": "Resveratrol reduced total testosterone by 28% — a magnitude comparable to first-line antiandrogen therapies, unusual for a dietary supplement with no prior PCOS-specific indication.",
  "mechanisms": [
    {"source": "resveratrol", "relation": "reduces", "target": "testosterone", "confidence": 0.9},
    {"source": "resveratrol", "relation": "improves", "target": "HOMA-IR", "confidence": 0.9},
    {"source": "resveratrol", "relation": "improves", "target": "menstrual regularity", "confidence": 0.9}
  ]
}

---

## Example 2 — Animal/mechanistic study, unclear direction

Source:
Title: Silibinin ameliorates PCOS-like phenotype in rat model via NF-κB inhibition
Journal: Molecular and Cellular Endocrinology
Year: 2022
Study type: Animal study
Abstract: Female Wistar rats were injected with DHEA to induce PCOS. Silibinin (100 or 200 mg/kg IP)
for 21 days significantly reduced ovarian cyst formation, restored estrous cycle, decreased
testosterone and LH/FSH ratio, and inhibited NF-κB and TNF-α. No human participants.

Output:
{
  "schema_version": "1.2",
  "population": "Female Wistar rats with DHEA-induced PCOS (animal model)",
  "population_diet": null,
  "population_bmi": null,
  "population_age_range": null,
  "population_comorbidities": [],
  "population_ethnicity": null,
  "n_total": null,
  "intervention": "silibinin",
  "comparator": "vehicle control",
  "main_outcomes": ["ovarian cyst formation", "estrous cycle", "testosterone", "LH/FSH ratio", "NF-kB activity", "TNF-alpha"],
  "effect_direction": "unclear",
  "limitations": ["animal model only (no human data)", "intraperitoneal injection (non-clinical route)", "DHEA-induced PCOS may not reflect all PCOS subtypes"],
  "reasoning_summary": "Animal study — effect_direction set to 'unclear' regardless of positive results because there are no human clinical outcomes. Results are mechanistically interesting (NF-kB inhibition) but cannot be extrapolated directly to patients. Population fields null because these are rats, not human participants.",
  "notable_finding": null,
  "mechanisms": [
    {"source": "silibinin", "relation": "inhibits", "target": "NF-kB", "confidence": 0.9},
    {"source": "silibinin", "relation": "reduces", "target": "TNF-alpha", "confidence": 0.9},
    {"source": "silibinin", "relation": "reduces", "target": "testosterone", "confidence": 0.85},
    {"source": "NF-kB", "relation": "associated_with", "target": "hyperandrogenism", "confidence": 0.7}
  ]
}

---

Now extract from the following source:
"""


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY RECORD (schema template shown to the model)
# ─────────────────────────────────────────────────────────────────────────────

def empty_extraction_record(canonical_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "canonical_id": canonical_id,
        "population": None,
        "population_diet": None,
        "population_bmi": None,
        "population_age_range": None,
        "population_comorbidities": [],
        "population_ethnicity": None,
        "n_total": None,
        "intervention": None,
        "comparator": None,
        "main_outcomes": [],
        "effect_direction": "unclear",
        "limitations": [],
        "reasoning_summary": None,
        "notable_finding": None,
        "mechanisms": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_source_text(
    row: dict[str, Any],
    fulltext: dict[str, Any] | None = None,
    max_abstract: int = 2000,
) -> str:
    """
    Build the source text block from an article row dict.

    fulltext: optional dict from article_fulltexts table with keys:
        abstract_full, methods_text, results_text, discussion_text, fetch_source
    When fulltext is provided the richer sections replace/augment the plain abstract.

    Cascade strategy:
      - abstract_full from fulltext > abstract_text from articles
      - methods_text  added when available (critical for BMI, n, ethnicity)
      - results_text  added when available
      - discussion_text added when available (limitations)
    """
    parts = []

    # ── Bibliographic header ──────────────────────────────────────────────────
    for label, key in (
        ("Title",         "title"),
        ("Journal",       "journal"),
        ("Year",          "year"),
        ("Study type",    "study_type"),
        ("Evidence tier", "evidence_tier"),
        ("Summary",       "summary_short"),
    ):
        value = row.get(key)
        if value not in (None, "", "[]"):
            parts.append(f"{label}: {value}")

    # ── Abstract: prefer richly-structured fulltext abstract ──────────────────
    abstract_full = (fulltext or {}).get("abstract_full")
    abstract_text = row.get("abstract_text")
    if abstract_full:
        parts.append(f"Abstract: {str(abstract_full)[:max_abstract]}")
    elif abstract_text:
        parts.append(f"Abstract: {str(abstract_text)[:max_abstract]}")

    # ── Full text sections (Methods, Results, Discussion) ─────────────────────
    if fulltext:
        source_label = fulltext.get("fetch_source", "")
        label_suffix = f" [{source_label}]" if source_label else ""

        if fulltext.get("methods_text"):
            parts.append(f"Methods{label_suffix}: {fulltext['methods_text'][:2500]}")
        if fulltext.get("results_text"):
            parts.append(f"Results{label_suffix}: {fulltext['results_text'][:2000]}")
        if fulltext.get("discussion_text"):
            parts.append(f"Discussion/Limitations{label_suffix}: {fulltext['discussion_text'][:1500]}")

    return "\n\n".join(parts)


def build_extraction_prompt(
    row: dict[str, Any],
    fulltext: dict[str, Any] | None = None,
) -> str:
    """
    Full extraction prompt for Gemma.
    Goes in the USER turn (system turn handled separately in _call_ollama).

    Structure:
      1. Few-shot examples (2 complete demonstrations)
      2. Field guidance (per-field instructions)
      3. Target schema (empty JSON to fill)
      4. Source text (the actual paper — abstract + fulltext sections if available)
    """
    field_guidance = "\n".join(
        f"- {field}: {instruction}" for field, instruction in EXTRACTION_FIELDS.items()
    )
    schema = json.dumps(
        empty_extraction_record(row.get("canonical_id")),
        ensure_ascii=False,
        indent=2,
    )
    source_text = build_source_text(row, fulltext=fulltext)

    # Order matters: examples → field guidance → source text → schema
    # Gemma reads top-to-bottom: instructions first, then apply to the actual paper.
    return (
        FEW_SHOT_EXAMPLES
        + "Field guidance (apply these rules to the source below):\n"
        + field_guidance
        + "\n\n---\n\nSource to extract:\n\n"
        + source_text
        + "\n\n---\n\n"
        + "Return ONLY the filled JSON below. No markdown fences, no explanation outside the JSON.\n\n"
        + "Target schema:\n"
        + schema
    )
