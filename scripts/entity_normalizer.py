"""
Entity Normalizer for the PCOS Research System
===============================================
Unifies variant names (e.g. "metformin", "glucophage", "Metformin XR")
into a single canonical entity so the anomaly scanner can count them
correctly.

Four layers:
  1. Seed dictionary   -- hand-curated aliases for ~50 key PCOS entities
  2. Fuzzy matching    -- Levenshtein distance catches typos / minor variants
  3. LLM resolution    -- Gemma decides if two terms are the same entity
  4. Role assignment   -- Gemma labels each entity's role in the article

Usage:
  python scripts/entity_normalizer.py                # full pipeline
  python scripts/entity_normalizer.py --skip-llm     # layers 1-2 only (fast)
  python scripts/entity_normalizer.py --seed-only     # layer 1 only (instant)
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

import requests
from rapidfuzz import fuzz, process

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "pcos_research.db"

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma4:31b-cloud"  # mismo modelo que run_ollama_article_labeling.py

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ===================================================================
# LAYER 1 -- SEED DICTIONARY
# ===================================================================
# Each entry: canonical_name -> {type, aliases}
# The canonical_name is the standard medical/scientific term.
# Aliases include brand names, abbreviations, common misspellings,
# and variant formulations that should all map to the same entity.
# -------------------------------------------------------------------

SEED: dict[str, dict] = {
    # ---- PHARMACOLOGICAL INTERVENTIONS ----
    "metformin": {
        "type": "intervention",
        "aliases": [
            "glucophage", "metformin xr", "metformin hcl",
            "metformin hydrochloride", "biguanide", "metformin er",
            "metformin 500 mg", "metformin 500 mg oral tablet",
            "metformin 850 mg", "metformin 1000 mg",
            "a combination of metformin",  # sometimes appears as raw term
        ],
    },
    "letrozole": {
        "type": "intervention",
        "aliases": ["femara", "letrozol"],
    },
    "clomiphene citrate": {
        "type": "intervention",
        "aliases": [
            "clomiphene", "clomid", "cc", "clomifene",
            "clomifene citrate", "serophene",
        ],
    },
    "spironolactone": {
        "type": "intervention",
        "aliases": ["aldactone", "spirolactone"],
    },
    "oral contraceptives": {
        "type": "intervention",
        "aliases": [
            "combined oral contraceptives", "coc", "oc", "ocp",
            "birth control pills", "oral contraceptive pills",
            "ethinyl estradiol", "ethynyl-estradiol", "ethynylestradiol",
            "drospirenone/ethinyl estradiol",
            "ethinylestradiol", "yasmin", "yaz", "diane-35",
            "cyproterone acetate/ethinylestradiol", "desogestrel",
            "drospirenone", "gestodene", "levonorgestrel",
        ],
    },
    "flutamide": {
        "type": "intervention",
        "aliases": ["eulexin"],
    },
    "bicalutamide": {
        "type": "intervention",
        "aliases": ["casodex", "bicalutamide 50 mg", "bica"],
    },
    "finasteride": {
        "type": "intervention",
        "aliases": ["propecia", "proscar"],
    },
    "liraglutide": {
        "type": "intervention",
        "aliases": ["saxenda", "victoza", "glp-1 agonist liraglutide"],
    },
    "semaglutide": {
        "type": "intervention",
        "aliases": ["ozempic", "wegovy", "rybelsus"],
    },
    "exenatide": {
        "type": "intervention",
        "aliases": ["byetta", "bydureon"],
    },
    "glp-1 receptor agonists": {
        "type": "intervention",
        "aliases": [
            "glp-1 ra", "glp-1 agonists", "glp1 agonist",
            "incretin mimetics",
        ],
    },
    "sglt2 inhibitors": {
        "type": "intervention",
        "aliases": [
            "sglt2i", "empagliflozin", "dapagliflozin",
            "canagliflozin", "sodium-glucose cotransporter 2 inhibitors",
        ],
    },
    "pioglitazone": {
        "type": "intervention",
        "aliases": ["actos", "thiazolidinedione", "tzd"],
    },
    "rosiglitazone": {
        "type": "intervention",
        "aliases": ["avandia"],
    },
    "gonadotropins": {
        "type": "intervention",
        "aliases": [
            "fsh", "recombinant fsh", "r-fsh", "hmg",
            "human menopausal gonadotropin", "gonal-f", "menopur",
            "follitropin alfa", "follitropin beta",
            "corifollitropin alfa", "corifollitropin",
            "recombinant human follicle stimulating hormone",
            "rhfsh", "r-hfsh", "urinary fsh", "highly purified fsh",
            "ufsh", "controlled ovarian stimulation",
        ],
    },
    "hcg": {
        "type": "intervention",
        "aliases": [
            "human chorionic gonadotropin", "pregnyl", "ovidrel",
            "choriogonadotropin alfa", "trigger shot",
            "rhcg", "r-hcg", "recombinant hcg",
            "recombinant human chorionic gonadotropin",
            "recombinant human choriogonadotropin",
        ],
    },
    "gnrh agonists": {
        "type": "intervention",
        "aliases": [
            "gnrh-a", "leuprolide", "triptorelin",
            "triptorelin acetate", "buserelin", "goserelin",
            "gnrh agonist", "gnrh-agonist", "long gnrh agonist",
            "gnrh agonist cycle", "long protocol gnrh agonist",
            "leuprolide acetate", "arvekap", "decapeptyl",
        ],
    },
    "gnrh antagonists": {
        "type": "intervention",
        "aliases": [
            "gnrh-ant", "cetrorelix", "ganirelix", "degarelix",
            "gnrh antagonist", "gnrh-antagonist", "gnrh antagonist protocol",
        ],
    },
    "berberine": {
        "type": "intervention",
        "aliases": ["berberine hydrochloride", "berberine hcl"],
    },
    "simvastatin": {
        "type": "intervention",
        "aliases": ["zocor", "statin"],
    },
    "atorvastatin": {
        "type": "intervention",
        "aliases": ["lipitor"],
    },
    "dihydroartemisinin": {
        "type": "intervention",
        "aliases": ["artemisinin derivative"],
        # Note: 'dha' alias removed -- collides with docosahexaenoic acid (omega-3)
    },
    "salsalate": {
        "type": "intervention",
        "aliases": ["disalcid", "salicylsalicylic acid"],
    },
    "mirabegron": {
        "type": "intervention",
        "aliases": ["myrbetriq", "beta-3 agonist"],
    },
    # ---- THIAZOLIDINEDIONES ----
    "pioglitazone": {
        "type": "intervention",
        "aliases": ["actos", "thiazolidinedione", "tzd"],
    },
    "rosiglitazone": {
        "type": "intervention",
        "aliases": ["avandia"],
    },
    # ---- DPP-4 INHIBITORS / INCRETINS ----
    "sitagliptin": {
        "type": "intervention",
        "aliases": ["januvia", "dpp-4 inhibitor", "dpp4 inhibitor"],
    },
    "tirzepatide": {
        "type": "intervention",
        "aliases": ["mounjaro", "twincretin", "gip/glp-1 agonist"],
    },
    # ---- WEIGHT LOSS / METABOLIC ----
    "orlistat": {
        "type": "intervention",
        "aliases": ["xenical", "alli", "lipase inhibitor"],
    },
    "acarbose": {
        "type": "intervention",
        "aliases": ["precose", "glucobay", "alpha-glucosidase inhibitor"],
    },
    # ---- STEROIDS / HORMONES ----
    "dexamethasone": {
        "type": "intervention",
        "aliases": ["decadron", "dexamethasone sodium phosphate"],
    },
    "hydrocortisone": {
        "type": "intervention",
        "aliases": ["cortisol", "cortef"],
    },
    "estradiol": {
        "type": "intervention",
        "aliases": [
            "estrace", "estradiol valerate", "estradiol benzoate",
            "17-beta estradiol", "e2", "oestradiol",
            "micronized estradiol",
        ],
    },
    "progesterone": {
        "type": "intervention",
        "aliases": [
            "micronized progesterone", "prometrium", "utrogestan",
            "progesterone in oil", "progestin", "natural progesterone",
            "progesterone capsule", "vaginal progesterone",
        ],
    },
    "dhea": {
        "type": "intervention",
        "aliases": [
            "dehydroepiandrosterone", "dehydroepiandrosterone (dhea)",
            "dehydroepiandrosterone sulfate", "dheas",
            "prasterone",
        ],
    },
    "cyproterone acetate": {
        "type": "intervention",
        "aliases": [
            "androcur", "cyproterone",
            "cyproterone acetate/ethinylestradiol",  # when used alone as antiandrogen
        ],
    },
    # ---- FERTILITY / ART ----
    "icsi": {
        "type": "intervention",
        "aliases": [
            "intracytoplasmic sperm injection",
            "icsi treatment", "icsi cycle",
        ],
    },
    "ivf": {
        "type": "intervention",
        "aliases": [
            "in vitro fertilization", "in-vitro fertilization",
            "ivf cycle", "ivf treatment", "art",
            "assisted reproductive technology",
        ],
    },
    # ---- DIETARY PATTERNS ----
    "intermittent fasting": {
        "type": "intervention",
        "aliases": [
            "if diet", "intermittent caloric restriction",
            "time-restricted eating", "5:2 diet",
        ],
    },
    # ---- SELECTIVE MODULATORS ----
    "raloxifene": {
        "type": "intervention",
        "aliases": ["evista", "serm"],
    },
    "roflumilast": {
        "type": "intervention",
        "aliases": ["daliresp", "daxas", "pde4 inhibitor"],
    },
    "sibutramine": {
        "type": "intervention",
        "aliases": ["meridia", "reductil"],
    },

    # ---- SUPPLEMENTS / NUTRACEUTICALS ----
    "myo-inositol": {
        "type": "intervention",
        "aliases": [
            "inositol", "myo inositol", "mi",
            "myo-inositol + d-chiro-inositol", "combined inositol",
            "inositol combination", "inofolic", "inofolic plus",
            "myoinositol", "myo-ins", "ovasitol",
        ],
    },
    "d-chiro-inositol": {
        "type": "intervention",
        "aliases": ["dci", "d chiro inositol", "d-chiro"],
    },
    "vitamin d": {
        "type": "intervention",
        "aliases": [
            "vitamin d3", "vitamin d2", "cholecalciferol",
            "ergocalciferol", "vit d", "25-oh vitamin d",
        ],
    },
    "omega-3": {
        "type": "intervention",
        "aliases": [
            "fish oil", "omega 3", "n-3 pufa", "epa/dha",
            "eicosapentaenoic acid", "docosahexaenoic acid",
        ],
    },
    "coenzyme q10": {
        "type": "intervention",
        "aliases": ["coq10", "ubiquinone", "ubiquinol"],
    },
    "folic acid": {
        "type": "intervention",
        "aliases": ["folate", "methylfolate", "vitamin b9"],
    },
    "probiotics": {
        "type": "intervention",
        "aliases": [
            "probiotic", "probiotic agent", "lactobacillus",
            "bifidobacterium", "synbiotic",
        ],
    },
    "n-acetyl cysteine": {
        "type": "intervention",
        "aliases": ["nac", "n-acetylcysteine", "acetylcysteine"],
    },
    "alpha-lipoic acid": {
        "type": "intervention",
        "aliases": [
            "ala", "lipoic acid", "thioctic acid",
            "alpha lipoic acid", "r-lipoic acid", "alpha-lipoate",
        ],
    },
    "curcumin": {
        "type": "intervention",
        "aliases": ["turmeric", "curcuminoids"],
    },
    "resveratrol": {
        "type": "intervention",
        "aliases": ["trans-resveratrol"],
    },
    "chromium": {
        "type": "intervention",
        "aliases": ["chromium picolinate", "chromium supplementation"],
    },
    "zinc": {
        "type": "intervention",
        "aliases": ["zinc supplementation", "zinc sulfate"],
    },
    "selenium": {
        "type": "intervention",
        "aliases": ["selenium supplementation", "selenomethionine"],
    },
    "cinnamon": {
        "type": "intervention",
        "aliases": ["cinnamomum", "cinnamon extract"],
    },

    # ---- PROCEDURES / BEHAVIORAL ----
    "laparoscopic ovarian drilling": {
        "type": "intervention",
        "aliases": ["lod", "ovarian drilling", "ovarian diathermy"],
    },
    "ivf": {
        "type": "intervention",
        "aliases": [
            "in vitro fertilization", "in-vitro fertilization",
            "in vitro fertilisation", "art",
        ],
    },
    "ivm": {
        "type": "intervention",
        "aliases": [
            "in vitro maturation", "in-vitro maturation", "capa-ivm",
            "ivm treatment", "ivm (in vitro maturation) treatment",
            "in vitro maturation (ivm)",
        ],
    },
    "bariatric surgery": {
        "type": "intervention",
        "aliases": [
            "gastric bypass", "sleeve gastrectomy",
            "laparoscopic sleeve gastrectomy", "roux-en-y",
            "metabolic surgery",
        ],
    },
    "lifestyle intervention": {
        "type": "intervention",
        "aliases": [
            "lifestyle", "lifestyle modification",
            "diet and exercise", "behavioral intervention",
            "lifestyle changes",
        ],
    },
    "dietary intervention": {
        "type": "intervention",
        "aliases": [
            "diet", "dietary", "caloric restriction",
            "low carbohydrate diet", "mediterranean diet",
            "dash diet", "ketogenic diet",
            "calorie restriction", "low calorie diet",
            "low-calorie diet", "high protein diet",
            "reduced glycemic load diet", "low glycemic diet",
        ],
    },
    "exercise": {
        "type": "intervention",
        "aliases": [
            "physical activity", "aerobic exercise",
            "resistance training", "hiit",
            "high intensity interval training",
            "strength training", "endurance training",
            "moderate exercise", "exercise training",
            "supervised exercise", "supervised exercise training",
            "supervised exercise training sessions",
            "exercise program", "exercise intervention",
            "physical training", "structured exercise",
        ],
    },
    "acupuncture": {
        "type": "intervention",
        "aliases": [
            "electroacupuncture", "electro-acupuncture",
            "traditional acupuncture",
        ],
    },
    "cognitive behavioral therapy": {
        "type": "intervention",
        "aliases": ["cbt", "psychological intervention"],
    },

    # ---- BIOMARKERS / OUTCOMES ----
    "homa-ir": {
        "type": "biomarker",
        "aliases": [
            "insulin resistance index", "homa ir",
            "homeostatic model assessment",
        ],
    },
    "testosterone": {
        "type": "biomarker",
        "aliases": [
            "total testosterone", "free testosterone",
            "serum testosterone", "androgen levels",
        ],
    },
    "shbg": {
        "type": "biomarker",
        "aliases": [
            "sex hormone binding globulin",
            "sex hormone-binding globulin",
        ],
    },
    "amh": {
        "type": "biomarker",
        "aliases": [
            "anti-mullerian hormone", "anti-muellerian hormone",
            "antimullerian hormone",
        ],
    },
    "bmi": {
        "type": "biomarker",
        "aliases": ["body mass index", "body-mass index"],
    },
    "menstrual regularity": {
        "type": "outcome",
        "aliases": [
            "menstrual cycle", "cycle regularity",
            "oligomenorrhea", "amenorrhea",
        ],
    },
    "ovulation rate": {
        "type": "outcome",
        "aliases": [
            "ovulation", "ovulatory rate", "ovulatory cycles",
        ],
    },
    "pregnancy rate": {
        "type": "outcome",
        "aliases": [
            "clinical pregnancy rate", "live birth rate",
            "fertility", "conception rate",
        ],
    },
    "hirsutism": {
        "type": "outcome",
        "aliases": [
            "ferriman-gallwey score", "f-g score",
            "modified ferriman-gallwey",
        ],
    },
    "acne": {
        "type": "outcome",
        "aliases": ["acne score", "acne vulgaris"],
    },
    "quality of life": {
        "type": "outcome",
        "aliases": ["qol", "hrqol", "health-related quality of life",
                     "pcosq", "sf-36"],
    },
    # ---- SUPPLEMENTS & NUTRACEUTICALS (added from new_entity review) ----
    "melatonin": {
        "type": "intervention",
        "aliases": [
            "melatonin supplementation", "melatonin 6 mg", "melatonin 3 mg",
            "melatonin treatment",
        ],
    },
    "magnesium": {
        "type": "intervention",
        "aliases": [
            "magnesium supplementation", "magnesium oxide", "magnesium citrate",
            "magnesium glycinate", "mg supplementation",
        ],
    },
    "l-carnitine": {
        "type": "intervention",
        "aliases": [
            "carnitine", "levocarnitine", "l carnitine",
            "acetyl-l-carnitine", "alcar",
        ],
    },
    "gaba": {
        "type": "intervention",
        "aliases": [
            "gaba supplementation", "gamma-aminobutyric acid",
            "gamma aminobutyric acid",
        ],
    },
    "nad+": {
        "type": "intervention",
        "aliases": [
            "nad", "nicotinamide adenine dinucleotide", "nmn",
            "nicotinamide mononucleotide", "nr", "nicotinamide riboside",
        ],
    },
    # ---- PHYTOESTROGENS & FLAVONOIDS ----
    "genistein": {
        "type": "intervention",
        "aliases": [
            "genistein supplementation", "genistein isoflavone",
            "soy isoflavone genistein",
        ],
    },
    "quercetin": {
        "type": "intervention",
        "aliases": [
            "quercetin supplementation", "quercetin flavonoid",
            "quercetin dihydrate",
        ],
    },
    # ---- PHARMACOLOGICAL (added from new_entity review) ----
    "cabergoline": {
        "type": "intervention",
        "aliases": [
            "cabergoline 0.5 mg", "dostinex", "cab",
            "dopamine agonist cabergoline",
        ],
    },
    "pentoxifylline": {
        "type": "intervention",
        "aliases": [
            "pentoxifylline (ptx)", "ptx", "trental",
        ],
    },
    "chiglitazar": {
        "type": "intervention",
        "aliases": [
            "chiglitazar sodium", "ppar agonist chiglitazar",
        ],
    },
    "humanin": {
        "type": "intervention",
        "aliases": [
            "humanin supplementation", "humanin peptide", "hn",
        ],
    },
    # ---- NEUROPEPTIDES ----
    "kisspeptin": {
        "type": "intervention",
        "aliases": [
            "kisspeptin 112-121", "kisspeptin-10", "kisspeptin-54",
            "kiss1", "metastin",
        ],
    },
    # ---- ALTERNATIVE THERAPIES ----
    "reflexology": {
        "type": "intervention",
        "aliases": [
            "foot reflexology", "reflexology therapy", "zone therapy",
        ],
    },
    # ---- ASSISTED REPRODUCTION PROCEDURES ----
    "frozen embryo transfer": {
        "type": "intervention",
        "aliases": [
            "fet", "frozen-thawed embryo transfer", "frozen et",
            "artificial frozen embryo transfer cycles",
            "natural cycle-frozen embryo transfer (nc-fet)",
            "modified natural cycle-frozen embryo transfer (mnc-fet)",
        ],
    },
    "fresh embryo transfer": {
        "type": "intervention",
        "aliases": [
            "fresh et", "fresh transfer", "fresh ivf transfer",
        ],
    },
}

# ===================================================================
# Pre-build a flat lookup: alias (lowercase) -> canonical_name
# ===================================================================

def _build_alias_map() -> dict[str, str]:
    """Create a flat dict: every known alias -> its canonical name."""
    m: dict[str, str] = {}
    for canonical, info in SEED.items():
        m[canonical.lower()] = canonical
        for alias in info.get("aliases", []):
            m[alias.lower()] = canonical
    return m

ALIAS_MAP: dict[str, str] = _build_alias_map()
# Also keep a list of all known lowercase names for fuzzy search
ALL_KNOWN_NAMES: list[str] = list(ALIAS_MAP.keys())


# ===================================================================
# LAYER 2 -- FUZZY MATCHING
# ===================================================================
# When an input string is NOT found in the alias map exactly,
# we use rapidfuzz to find the closest known alias.
# "score_cutoff" is the minimum similarity (0-100) to accept a match.
# 80 is a good balance: catches "metformn" -> "metformin" (score ~93)
# but rejects "vitamin d" -> "vitamin k" (score ~73).
# -------------------------------------------------------------------

FUZZY_CUTOFF = 80  # minimum similarity score (0-100) to accept


def resolve_by_dictionary(raw_term: str) -> tuple[str | None, str, float]:
    """
    Try to resolve a raw term using layers 1 and 2.

    Returns (canonical_name | None, method, confidence).
      method is "exact", "fuzzy", or "unknown".
      confidence is 0.0 - 1.0.
    """
    if not raw_term or not raw_term.strip():
        return None, "empty", 0.0

    cleaned = raw_term.strip().lower()

    # Layer 1: exact match in alias map
    if cleaned in ALIAS_MAP:
        return ALIAS_MAP[cleaned], "exact", 1.0

    # Layer 2: fuzzy match
    result = process.extractOne(
        cleaned,
        ALL_KNOWN_NAMES,
        scorer=fuzz.WRatio,        # Weighted Ratio: handles partial matches
        score_cutoff=FUZZY_CUTOFF,
    )
    if result is not None:
        best_alias, score, _idx = result
        canonical = ALIAS_MAP[best_alias]
        confidence = round(score / 100.0, 3)
        return canonical, "fuzzy", confidence

    return None, "unknown", 0.0


# ===================================================================
# LAYER 3 -- LLM RESOLUTION (Gemma via Ollama)
# ===================================================================
# For terms that layers 1-2 couldn't match, we ask Gemma:
#   "Is <unknown_term> the same entity as any of these known entities?"
# Gemma returns JSON with its answer.
# -------------------------------------------------------------------

def _call_ollama(user_prompt: str,
                 system_prompt: str = "You are a biomedical entity resolver. Reply with valid JSON only.",
                 max_retries: int = 3) -> str | None:
    """
    Send a chat request to Ollama (cloud model gemma4:31b-cloud).
    Retries on timeouts / transient errors with exponential backoff.
    Returns the assistant message content (markdown fences stripped),
    or None on failure.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 220,
            "num_ctx": 1536,
        },
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=240)
            resp.raise_for_status()
            body = resp.json()
            content = ((body.get("message") or {}).get("content") or "").strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            return content
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            # Includes 500 server errors (Ollama cloud overloaded) — retry with backoff
            wait = 2 ** attempt  # 2, 4, 8 seconds
            log.warning("Ollama error (attempt %d/%d): %s. Retrying in %ds...",
                        attempt, max_retries, e.__class__.__name__, wait)
            time.sleep(wait)
        except Exception as e:
            log.warning("Ollama call failed (non-retryable): %s", e)
            return None

    log.error("Ollama call gave up after %d retries", max_retries)
    return None


def resolve_by_llm(raw_term: str, top_candidates: list[str] | None = None) -> tuple[str | None, float, str, str | None]:
    """
    Layer 3: Ask Gemma to classify an unknown term with 3 possible outcomes:

      action="alias"   → raw_term is an alias/variant of an existing entity
                         (returns canonical name + confidence)
      action="new"     → raw_term is a REAL biomedical entity worth adding.
                         Must also return entity_type:
                           "intervention"    — drug, supplement, behavioral therapy, procedure
                           "diagnostic_test" — lab test, imaging, scoring instrument
                           "comorbidity"     — concurrent condition / comorbidity
                           "phenotype"       — PCOS subtype or patient phenotype descriptor
      action="discard" → raw_term is noise (placebo, codes, ML terms, measurements, etc.)
                         (returns None, 0.0, entity_type=None)

    Returns (canonical_name | None, confidence, action, entity_type | None).
    """
    if top_candidates is None:
        top_candidates = list(SEED.keys())

    candidates_str = ", ".join(top_candidates[:40])

    prompt = (
        "You are a biomedical entity classifier for a PCOS (polycystic ovary syndrome) research database.\n"
        "Your task: decide what to do with a RAW TERM extracted from a clinical study.\n\n"
        "THREE possible actions:\n"
        '  "alias"   → the term is a variant/brand name/dosage of an EXISTING entity in the list.\n'
        '              Examples: "metformin 500mg"="metformin", "saxenda"="liraglutide"\n'
        '  "new"     → the term is a REAL biomedical entity NOT in the list, worth adding.\n'
        '              You MUST also specify entity_type:\n'
        '              - "intervention"   : drug, supplement, nutraceutical, surgical/behavioral procedure\n'
        '              - "diagnostic_test": laboratory test, imaging study, clinical scoring instrument\n'
        '              - "comorbidity"    : a co-occurring disease or metabolic condition\n'
        '              - "phenotype"      : PCOS subtype or well-defined patient characteristic\n'
        '  "discard" → the term is NOT a meaningful biomedical entity. Discard if it is:\n'
        '              * placebo or control arm ("placebo pill", "saline injection", "sham")\n'
        '              * the condition itself ("pcos", "polycystic ovary syndrome")\n'
        '              * measurement / outcome value ("serum androgen level", "bmi score")\n'
        '              * control group description ("women without pcos", "healthy controls")\n'
        '              * protein/structure database code ("1fgd", "2rgw", "1rlw", "1h-nmr")\n'
        '              * machine learning method ("transfer learning", "random forest", "cnn",\n'
        '                "stacking ensemble", "xgboost", "logistic regression", "svm")\n'
        '              * measurement procedure or monitoring device\n'
        '                ("24-hour ambulatory blood pressure monitoring", "eeg recording")\n'
        '              * garbled text fragment (starts with "/", ")", contains unclosed "(")\n'
        '              * generic non-specific text ("usual care", "follow-up", "water", "3 meals",\n'
        '                "food supplements", "nutritional supplements", "natural supplementation")\n\n'
        "EXISTING ENTITIES (pick one for alias action):\n"
        f"{candidates_str}\n\n"
        "EXAMPLES — read carefully:\n"
        '  RAW: "metformin 1500 mg"         -> {"action":"alias","canonical":"metformin","confidence":0.98}\n'
        '  RAW: "saxenda"                   -> {"action":"alias","canonical":"liraglutide","confidence":0.99}\n'
        '  RAW: "micronized progesterone"   -> {"action":"alias","canonical":"progesterone","confidence":0.95}\n'
        '  RAW: "kisspeptin 112-121"        -> {"action":"new","entity_type":"intervention","confidence":0.88}\n'
        '  RAW: "nicotinamide riboside"     -> {"action":"new","entity_type":"intervention","confidence":0.82}\n'
        '  RAW: "lean pcos phenotype"       -> {"action":"new","entity_type":"phenotype","confidence":0.90}\n'
        '  RAW: "classic pcos (type a)"     -> {"action":"new","entity_type":"phenotype","confidence":0.85}\n'
        '  RAW: "insulin resistance"        -> {"action":"new","entity_type":"comorbidity","confidence":0.90}\n'
        '  RAW: "non-alcoholic fatty liver" -> {"action":"new","entity_type":"comorbidity","confidence":0.88}\n'
        '  RAW: "thyroid ultrasound"        -> {"action":"new","entity_type":"diagnostic_test","confidence":0.92}\n'
        '  RAW: "anti-mullerian hormone"    -> {"action":"new","entity_type":"diagnostic_test","confidence":0.93}\n'
        '  RAW: "oral glucose tolerance test"             -> {"action":"discard","reason":"measurement procedure"}\n'
        '  RAW: "placebo oral tablet"                     -> {"action":"discard","reason":"placebo control"}\n'
        '  RAW: "polycystic ovary syndrome (pcos)"        -> {"action":"discard","reason":"the condition itself"}\n'
        '  RAW: "women without pcos"                      -> {"action":"discard","reason":"control group"}\n'
        '  RAW: "serum androgen measurement"              -> {"action":"discard","reason":"measurement"}\n'
        '  RAW: "1fgd"                                    -> {"action":"discard","reason":"protein structure code"}\n'
        '  RAW: "2rgw"                                    -> {"action":"discard","reason":"database code"}\n'
        '  RAW: "1rlw"                                    -> {"action":"discard","reason":"alphanumeric code"}\n'
        '  RAW: "transfer learning"                       -> {"action":"discard","reason":"ML algorithm"}\n'
        '  RAW: "stacking ensemble)"                      -> {"action":"discard","reason":"garbled ML text"}\n'
        '  RAW: "extended machine learning (cnn)"         -> {"action":"discard","reason":"ML method"}\n'
        '  RAW: "24-hour ambulatory blood pressure monitoring" -> {"action":"discard","reason":"monitoring device"}\n'
        '  RAW: "3 meals"                                 -> {"action":"discard","reason":"generic dietary description"}\n'
        '  RAW: "food supplements"                        -> {"action":"discard","reason":"too generic"}\n'
        '  RAW: "controlling chronic low-grade inflammation" -> {"action":"discard","reason":"process description"}\n\n'
        f'RAW: "{raw_term}"\n'
        "Reply with JSON only — no explanation outside the JSON:\n"
        '{"action":"alias"|"new"|"discard",\n'
        ' "canonical":"<entity_name>" (only when action=alias),\n'
        ' "entity_type":"intervention"|"diagnostic_test"|"comorbidity"|"phenotype" (only when action=new),\n'
        ' "confidence":0.0-1.0,\n'
        ' "reason":"..." (only when action=discard)}\n'
    )

    response = _call_ollama(prompt)
    if not response:
        return None, 0.0, "error", None

    try:
        data = json.loads(response)
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            return None, 0.0, "parse_error", None

        action = (data.get("action") or "discard").strip().lower()

        if action == "alias":
            canonical = (data.get("canonical") or "").strip().lower()
            conf = float(data.get("confidence", 0.0))
            candidates_lower = [c.lower() for c in top_candidates]
            if canonical in candidates_lower and conf >= 0.6:
                idx = candidates_lower.index(canonical)
                return top_candidates[idx], conf, "alias", None
            return None, 0.0, "alias_invalid", None

        elif action == "new":
            conf = float(data.get("confidence", 0.5))
            etype = (data.get("entity_type") or "intervention").strip().lower()
            valid_types = {"intervention", "diagnostic_test", "comorbidity", "phenotype"}
            if etype not in valid_types:
                etype = "intervention"
            return None, conf, "new", etype

        else:  # discard or anything unrecognized
            return None, 0.0, "discard", None

    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        log.warning("Could not parse LLM response: %s", response[:200])
        return None, 0.0, "parse_error", None


# ===================================================================
# LAYER 4 -- ROLE ASSIGNMENT
# ===================================================================
# For each entity found in an article, Gemma assigns its role:
#   intervention, outcome, biomarker, comparator, or population.
# The seed dictionary already has a default type, but the ROLE can
# vary by context (e.g. "metformin" is usually an intervention,
# but in a pharmacokinetics study it could be the subject).
# -------------------------------------------------------------------

VALID_ROLES = {"intervention", "outcome", "biomarker", "comparator", "population"}


def assign_role_from_seed(canonical_name: str) -> str | None:
    """Return the default role from the seed dictionary."""
    info = SEED.get(canonical_name)
    if info:
        return info.get("type")
    return None


def assign_role_by_llm(entity_name: str, context_snippet: str) -> tuple[str, float]:
    """
    Layer 4: Ask Gemma what role this entity plays in the given context.

    Returns (role, confidence).
    """
    prompt = (
        "You are classifying the ROLE of a biomedical entity in a PCOS study.\n"
        "Possible roles: intervention, outcome, biomarker, comparator, population.\n\n"
        f"ENTITY: {entity_name}\n"
        f"CONTEXT: {context_snippet[:500]}\n\n"
        "Reply with JSON only:\n"
        '{"role": "<one of the roles>", "confidence": 0.0-1.0}\n'
    )

    response = _call_ollama(prompt)
    if not response:
        return "intervention", 0.0  # safe default for PCOS research

    try:
        data = json.loads(response)
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            return "intervention", 0.0
        role = (data.get("role") or "intervention").lower().strip()
        conf = float(data.get("confidence", 0.0))
        if role not in VALID_ROLES:
            role = "intervention"
        return role, conf
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return "intervention", 0.0


# ===================================================================
# DATABASE OPERATIONS
# ===================================================================

def init_db(conn: sqlite3.Connection) -> None:
    """Create the three entity tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entity (
            entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            entity_type TEXT,
            aliases     TEXT,
            mesh_id     TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS article_entity_links (
            link_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_id  TEXT,
            entity_id     INTEGER REFERENCES entity(entity_id),
            role          TEXT,
            context_snippet TEXT,
            confidence    REAL,
            method        TEXT,
            raw_term      TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS intervention_signals (
            entity_id        INTEGER PRIMARY KEY REFERENCES entity(entity_id),
            n_studies        INTEGER DEFAULT 0,
            n_favorable      INTEGER DEFAULT 0,
            consistency_score REAL DEFAULT 0.0,
            weighted_score   REAL DEFAULT 0.0,
            last_updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    log.info("DB tables ready (entity, article_entity_links, intervention_signals)")


def upsert_entity(conn: sqlite3.Connection, canonical_name: str,
                   entity_type: str | None, aliases: list[str]) -> int:
    """Insert or update an entity. Returns entity_id."""
    row = conn.execute(
        "SELECT entity_id, aliases FROM entity WHERE canonical_name = ?",
        (canonical_name,),
    ).fetchone()

    aliases_json = json.dumps(sorted(set(aliases)), ensure_ascii=False)

    if row:
        # Merge aliases
        existing = set(json.loads(row[1])) if row[1] else set()
        merged = sorted(existing | set(aliases))
        conn.execute(
            "UPDATE entity SET aliases = ?, entity_type = COALESCE(?, entity_type) WHERE entity_id = ?",
            (json.dumps(merged, ensure_ascii=False), entity_type, row[0]),
        )
        return row[0]
    else:
        cur = conn.execute(
            "INSERT INTO entity (canonical_name, entity_type, aliases) VALUES (?, ?, ?)",
            (canonical_name, entity_type, aliases_json),
        )
        return cur.lastrowid


def insert_link(conn: sqlite3.Connection, canonical_id: str,
                entity_id: int, role: str, context_snippet: str,
                confidence: float, method: str, raw_term: str) -> None:
    """Insert an article-entity link (skip duplicates)."""
    exists = conn.execute(
        "SELECT 1 FROM article_entity_links WHERE canonical_id = ? AND entity_id = ? AND role = ?",
        (canonical_id, entity_id, role),
    ).fetchone()
    if exists:
        return
    conn.execute(
        """INSERT INTO article_entity_links
           (canonical_id, entity_id, role, context_snippet, confidence, method, raw_term)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (canonical_id, entity_id, role, context_snippet, confidence, method, raw_term),
    )


# ===================================================================
# INTERVENTION SPLITTER (v3)
# ===================================================================
# Many raw_terms are combos: "metformin + clomiphene citrate",
# "inositol + folic acid", "lifestyle versus metformin".
# We split them into individual terms before normalizing, so each
# component gets its own link.
# -------------------------------------------------------------------

import re as _re

_SPLIT_PATTERNS = _re.compile(
    r'\s*(?:'
    r'\bversus\b|\bvs\.?\b|\bvs\b'  # versus / vs
    r'|\band\b'                       # and (but not inside names)
    r'|\bplus\b'                      # plus
    r'|\bcombined with\b'             # combined with
    r'|\bwith\b'                      # with
    r'|[+;]'                          # + or ;
    r')\s*',
    flags=_re.IGNORECASE,
)

# These words when alone are noise, not real interventions
_SPLIT_NOISE = {
    "placebo", "control", "standard care", "usual care",
    "folic acid", "vitamin b9",  # common add-ons, usually not the main intervention
}

def split_intervention(raw_term: str) -> list[str]:
    """
    Split a potentially combined intervention into individual terms.

    Returns a list of 1+ terms. If no split pattern is found, returns
    the original term in a single-element list.

    Examples:
      "metformin + clomiphene citrate" -> ["metformin", "clomiphene citrate"]
      "lifestyle versus placebo"       -> ["lifestyle intervention"]
      "inositol + folic acid"          -> ["inositol"]  (folic acid filtered)
      "letrozole"                      -> ["letrozole"]
    """
    # Don't split very short terms (abbreviations like "r-fsh + hmg" ok)
    # or terms that are likely a single entity name
    parts = _SPLIT_PATTERNS.split(raw_term)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        return [raw_term.strip()]

    # Filter noise parts but keep at least one
    cleaned = [p for p in parts if p.lower() not in _SPLIT_NOISE and len(p) > 2]
    return cleaned if cleaned else [raw_term.strip()]


# ===================================================================
# EXTRACTION HELPERS
# ===================================================================

def extract_terms_from_trials(conn: sqlite3.Connection) -> list[dict]:
    """Pull intervention terms from the trials table."""
    rows = conn.execute("""
        SELECT nct_id, normalized_interventions, title
        FROM trials
        WHERE normalized_interventions IS NOT NULL
          AND normalized_interventions != '[]'
          AND normalized_interventions != ''
    """).fetchall()

    terms = []
    for nct_id, interventions_json, title in rows:
        try:
            items = json.loads(interventions_json)
        except (json.JSONDecodeError, TypeError):
            continue
        for item in items:
            if not item or not item.strip():
                continue
            # v3: split combined interventions before normalizing
            for sub_term in split_intervention(item.strip()):
                terms.append({
                    "source_id": nct_id,
                    "raw_term": sub_term,
                    "context": title or "",
                    "source_table": "trials",
                })
    return terms


def extract_terms_from_extractions(conn: sqlite3.Connection) -> list[dict]:
    """Pull intervention/comparator terms from article_extractions."""
    rows = conn.execute("""
        SELECT canonical_id, intervention, comparator,
               (SELECT title FROM articles a WHERE a.canonical_id = ae.canonical_id) as title
        FROM article_extractions ae
        WHERE intervention IS NOT NULL AND intervention != 'None' AND intervention != ''
    """).fetchall()

    terms = []
    for canonical_id, intervention, comparator, title in rows:
        for sub_term in split_intervention(intervention.strip()):
            terms.append({
                "source_id": canonical_id,
                "raw_term": sub_term,
                "context": title or "",
                "source_table": "article_extractions",
            })
        if comparator and comparator.strip() and comparator != "None":
            for sub_term in split_intervention(comparator.strip()):
                terms.append({
                    "source_id": canonical_id,
                    "raw_term": sub_term,
                    "context": title or "",
                    "source_table": "article_extractions",
                })
    return terms


# Noise terms to skip (not real interventions)
# These are: placebos, diagnostic tests, outcome measurements, condition names,
# control group descriptions — NOT things we can link to an intervention entity.
NOISE_TERMS = {
    # Placebos and controls
    "placebo", "placebo oral tablet", "placebo pills", "placebo capsule",
    "placebo tablet", "placebo metformin", "placebo liraglutide pen injector",
    "placebo injection", "placebo cream", "control", "sham",
    "usual care", "standard care", "standard of care", "no intervention",
    "water", "normal saline", "vehicle control",
    # The condition itself
    "pcos", "polycystic ovary syndrome", "polycystic ovary syndrome (pcos)",
    "polycystic ovarian syndrome", "pcos patients",
    # Control/comparison groups
    "control group", "control group without pcos", "women without pcos",
    "healthy controls", "non-pcos women", "comparison group",
    # Diagnostic tests (not interventions)
    "oral glucose tolerance test", "ogtt", "glucose tolerance test",
    "transvaginal ultrasound", "ultrasound", "blood draw", "blood test",
    "serum", "blood sample", "blood sample collection", "phlebotomy",
    "urine collection", "biopsy", "endometrium biopsy",
    "physical examination", "screening", "screening program",
    "physical activity measurement", "body composition measurement",
    "measurement of bisphenol in urine",
    # Observations / follow-up
    "observation", "follow-up", "baseline", "follow up",
    # Questionnaires / outcomes as process
    "questionnaire", "questionnaires", "survey",
    # Noise / empty
    "null", "", "none",
}

# Also catch noise by substring (for longer noisy terms)
NOISE_SUBSTRINGS = (
    "questionnaire", "assessment tool", "score according to",
    "comparison of leuco", "information about clinical risk",
    "developmental score", "ages & stages",
)


def is_noise(term: str) -> bool:
    """Return True if the term is noise (not a real intervention)."""
    t = term.strip().lower()
    if t in NOISE_TERMS:
        return True
    if len(t) < 3:
        return True
    if any(sub in t for sub in NOISE_SUBSTRINGS):
        return True
    return False


# ===================================================================
# MAIN PIPELINE
# ===================================================================

def seed_entities(conn: sqlite3.Connection) -> dict[str, int]:
    """Layer 1: Load all seed entities into the DB. Returns name->id map."""
    name_to_id: dict[str, int] = {}
    for canonical, info in SEED.items():
        eid = upsert_entity(
            conn, canonical, info["type"], info.get("aliases", [])
        )
        name_to_id[canonical] = eid
    conn.commit()
    log.info("Seeded %d canonical entities into DB", len(name_to_id))
    return name_to_id


def process_terms(conn: sqlite3.Connection, terms: list[dict],
                  name_to_id: dict[str, int],
                  use_llm: bool = True) -> dict:
    """
    Run all terms through the 4-layer pipeline.
    Returns stats dict.
    """
    stats = {
        "total": 0, "exact": 0, "fuzzy": 0, "fuzzy_verified": 0,
        "fuzzy_rejected": 0, "llm": 0, "unknown": 0, "noise": 0,
    }

    FUZZY_HIGH_CONF = 0.93   # >= this: accept fuzzy without LLM check
    # Below 0.93: ask Gemma to verify (catches false positives like
    # "salsalate" -> "alpha-lipoic acid", "mirabegron" -> "myo-inositol")
    # Raised from 0.90 after audit found ~5-8% false positives in 0.90 zone.

    # Collect unknowns for batch LLM (layer 3)
    unknowns: list[dict] = []
    # Collect low-confidence fuzzy matches for LLM verification
    fuzzy_to_verify: list[tuple[dict, str, float]] = []  # (term, canonical, conf)

    log.info("Processing %d raw terms through layers 1-2...", len(terms))

    for t in terms:
        stats["total"] += 1
        raw = t["raw_term"]

        if is_noise(raw):
            stats["noise"] += 1
            continue

        canonical, method, confidence = resolve_by_dictionary(raw)

        if canonical and method == "exact":
            stats["exact"] += 1
            if canonical not in name_to_id:
                eid = upsert_entity(conn, canonical, None, [raw.lower()])
                name_to_id[canonical] = eid
            role = assign_role_from_seed(canonical) or "intervention"
            insert_link(
                conn, t["source_id"], name_to_id[canonical],
                role, t["context"][:300], confidence, method, raw,
            )
        elif canonical and method == "fuzzy" and confidence >= FUZZY_HIGH_CONF:
            # High-confidence fuzzy: accept directly
            stats["fuzzy"] += 1
            if canonical not in name_to_id:
                eid = upsert_entity(conn, canonical, None, [raw.lower()])
                name_to_id[canonical] = eid
            role = assign_role_from_seed(canonical) or "intervention"
            insert_link(
                conn, t["source_id"], name_to_id[canonical],
                role, t["context"][:300], confidence, method, raw,
            )
        elif canonical and method == "fuzzy" and confidence < FUZZY_HIGH_CONF:
            # Low-confidence fuzzy: needs LLM verification
            fuzzy_to_verify.append((t, canonical, confidence))
        else:
            unknowns.append(t)

    conn.commit()
    log.info("Layer 1-2 results: %d exact, %d high-conf fuzzy, %d low-conf fuzzy (need LLM), %d noise, %d unknown",
             stats["exact"], stats["fuzzy"], len(fuzzy_to_verify), stats["noise"], len(unknowns))

    # Layer 2.5: LLM verification of low-confidence fuzzy matches
    if use_llm and fuzzy_to_verify:
        log.info("Verifying %d low-confidence fuzzy matches with LLM...", len(fuzzy_to_verify))
        for i, (t, fuzzy_canonical, fuzzy_conf) in enumerate(fuzzy_to_verify):
            raw = t["raw_term"]

            # NEW PROMPT (v2): "choose from list" format with few-shot examples.
            # Empirically the same model is far more accurate when it can pick
            # from candidates than when answering yes/no.
            # We give it the fuzzy candidate plus 2 plausible alternatives and
            # an explicit "none" option to avoid forced-choice bias.
            other_candidates = [
                c for c in SEED.keys() if c != fuzzy_canonical
            ][:6]
            candidates_for_llm = [fuzzy_canonical] + other_candidates[:2]

            prompt = (
                "You group medical terms into canonical entities for PCOS research.\n"
                "Two terms are the SAME entity if they refer to the same drug,\n"
                "drug class, supplement, procedure, or concept -- including:\n"
                "  - brand names vs generic (e.g. 'ozempic' = 'semaglutide')\n"
                "  - abbreviations (e.g. 'r-fsh' = 'fsh' = 'gonadotropins')\n"
                "  - dose/formulation variants ('metformin 500mg' = 'metformin')\n"
                "  - drug-class members ('corifollitropin alfa' = 'gonadotropins')\n"
                "  - protocol names that describe drug use\n"
                "    ('gnrh antagonist protocol' = 'gnrh antagonists')\n"
                "  - synonyms / typos ('rhcg' = 'hcg', 'inofolic' = 'myo-inositol')\n"
                "Different entities: incidental keyword overlap\n"
                "  ('oral smear' is NOT 'oral contraceptives')\n"
                "  ('measurement of X' is NOT a treatment)\n"
                "  ('placebo' is NOT a real intervention).\n\n"
                "EXAMPLES:\n"
                '  TERM "metformin 500 mg oral tablet" vs ["metformin", "letrozole", "myo-inositol"]\n'
                '    -> {"choice": "metformin"}\n'
                '  TERM "salsalate" vs ["alpha-lipoic acid", "metformin", "berberine"]\n'
                '    -> {"choice": "none"}\n'
                '  TERM "long gnrh agonist protocol" vs ["gnrh agonists", "gonadotropins", "hcg"]\n'
                '    -> {"choice": "gnrh agonists"}\n'
                '  TERM "blood sample collection" vs ["lifestyle intervention", "exercise", "ivm"]\n'
                '    -> {"choice": "none"}\n\n'
                f'TERM "{raw}" vs {json.dumps(candidates_for_llm)}\n'
                'Reply JSON only: {"choice": "<one of the candidates>" or "none"}\n'
            )
            response = _call_ollama(prompt)

            verified = False
            if response:
                try:
                    data = json.loads(response)
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    if isinstance(data, dict):
                        choice = (data.get("choice") or "").strip().lower()
                        if choice == fuzzy_canonical.lower():
                            verified = True
                except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                    pass

            if verified:
                stats["fuzzy_verified"] += 1
                if fuzzy_canonical not in name_to_id:
                    eid = upsert_entity(conn, fuzzy_canonical, None, [raw.lower()])
                    name_to_id[fuzzy_canonical] = eid
                role = assign_role_from_seed(fuzzy_canonical) or "intervention"
                insert_link(
                    conn, t["source_id"], name_to_id[fuzzy_canonical],
                    role, t["context"][:300], fuzzy_conf, "fuzzy_verified", raw,
                )
            else:
                stats["fuzzy_rejected"] += 1
                # Move to unknowns for layer 3 full resolution
                unknowns.append(t)
                log.info("  REJECTED fuzzy: '%s' is NOT '%s'", raw, fuzzy_canonical)

            if (i + 1) % 10 == 0:
                conn.commit()
                log.info("  Fuzzy verify progress: %d / %d", i + 1, len(fuzzy_to_verify))
                time.sleep(0.2)

        conn.commit()
        log.info("Fuzzy verification: %d confirmed, %d rejected (moved to unknowns)",
                 stats["fuzzy_verified"], stats["fuzzy_rejected"])
    elif fuzzy_to_verify:
        # No LLM available: accept all fuzzy as-is (old behavior)
        for t, fuzzy_canonical, fuzzy_conf in fuzzy_to_verify:
            stats["fuzzy"] += 1
            if fuzzy_canonical not in name_to_id:
                eid = upsert_entity(conn, fuzzy_canonical, None, [t["raw_term"].lower()])
                name_to_id[fuzzy_canonical] = eid
            role = assign_role_from_seed(fuzzy_canonical) or "intervention"
            insert_link(
                conn, t["source_id"], name_to_id[fuzzy_canonical],
                role, t["context"][:300], fuzzy_conf, "fuzzy", t["raw_term"],
            )
        conn.commit()
        log.info("Accepted %d low-conf fuzzy without verification (--skip-llm)", len(fuzzy_to_verify))

    # Layer 3: LLM resolution for unknowns
    if use_llm and unknowns:
        # v3 RESUMABILITY: skip terms already processed in a previous run
        already_done_keys = set()
        done_rows = conn.execute(
            "SELECT canonical_id, raw_term FROM article_entity_links "
            "WHERE method IN ('llm', 'new_entity')"
        ).fetchall()
        for cid, rt in done_rows:
            already_done_keys.add((cid, (rt or "").lower()))

        resumable_unknowns = [
            t for t in unknowns
            if (t["source_id"], t["raw_term"].lower()) not in already_done_keys
        ]
        skipped = len(unknowns) - len(resumable_unknowns)
        if skipped:
            log.info("Resuming: skipped %d already-processed unknowns, %d remaining",
                     skipped, len(resumable_unknowns))
        unknowns = resumable_unknowns

        log.info("Running LLM resolution on %d unknown terms...", len(unknowns))
        n_alias = n_new = n_discard = n_error = 0

        for i, t in enumerate(unknowns):
            raw = t["raw_term"]

            # Layer 3: 3-way classification
            # resolve_by_llm returns (canonical, conf, action, entity_type)
            canonical, conf, action, new_entity_type = resolve_by_llm(raw)

            if action == "alias" and canonical:
                # --- ALIAS: maps to an existing seed entity ---
                n_alias += 1
                stats["llm"] += 1
                if canonical not in name_to_id:
                    eid = upsert_entity(conn, canonical, None, [raw.lower()])
                    name_to_id[canonical] = eid
                # Permanently add as alias so future runs catch it at layer 1
                eid = name_to_id[canonical]
                existing = conn.execute(
                    "SELECT aliases FROM entity WHERE entity_id = ?", (eid,)
                ).fetchone()
                if existing and existing[0]:
                    aliases = set(json.loads(existing[0]))
                    aliases.add(raw.lower())
                    conn.execute(
                        "UPDATE entity SET aliases = ? WHERE entity_id = ?",
                        (json.dumps(sorted(aliases), ensure_ascii=False), eid),
                    )
                role = assign_role_from_seed(canonical) or "intervention"
                insert_link(
                    conn, t["source_id"], name_to_id[canonical],
                    role, t["context"][:300], conf, "llm", raw,
                )
                log.debug("  ALIAS: '%s' -> '%s' (conf=%.2f)", raw, canonical, conf)

            elif action == "new":
                # --- NEW ENTITY: real biomedical entity not in seed ---
                # entity_type can be: intervention, diagnostic_test, comorbidity, phenotype
                n_new += 1
                stats["unknown"] += 1
                new_canonical = raw.strip().lower()
                etype = new_entity_type or "intervention"
                if new_canonical not in name_to_id:
                    eid = upsert_entity(conn, new_canonical, etype, [])
                    name_to_id[new_canonical] = eid
                # Role in the link mirrors entity_type (interventions get role="intervention")
                link_role = "intervention" if etype == "intervention" else etype
                insert_link(
                    conn, t["source_id"], name_to_id[new_canonical],
                    link_role, t["context"][:300], conf, "new_entity", raw,
                )
                log.debug("  NEW ENTITY [%s]: '%s'", etype, raw)

            else:
                # --- DISCARD: noise, diagnostic, condition, placebo ---
                n_discard += 1
                log.debug("  DISCARDED: '%s' (action=%s)", raw, action)

            # Progress + rate limit
            if (i + 1) % 10 == 0:
                conn.commit()
                log.info("  LLM progress: %d / %d", i + 1, len(unknowns))
                time.sleep(0.2)  # gentle on Ollama

        conn.commit()
        log.info(
            "Layer 3 results: %d aliased to seed | %d new entities | %d discarded as noise",
            n_alias, n_new, n_discard,
        )
        log.info("Layer 3 totals: llm=%d, new_entity=%d",
                 stats["llm"], stats["unknown"])
    elif unknowns:
        stats["unknown"] = len(unknowns)
        log.info("Skipping LLM layer (--skip-llm). %d terms unresolved.", len(unknowns))

    return stats


def compute_signals(conn: sqlite3.Connection) -> None:
    """
    Aggregate article_entity_links + article_extractions to fill
    intervention_signals table.
    """
    log.info("Computing intervention signals...")

    # Clear old signals
    conn.execute("DELETE FROM intervention_signals")

    # For each entity that has role='intervention', count linked articles
    # and check effect_direction from article_extractions
    conn.execute("""
        INSERT INTO intervention_signals (entity_id, n_studies, n_favorable,
                                          consistency_score, weighted_score, last_updated)
        SELECT
            ael.entity_id,
            COUNT(DISTINCT ael.canonical_id) as n_studies,
            COUNT(DISTINCT CASE
                WHEN ae.effect_direction = 'favorable' THEN ael.canonical_id
            END) as n_favorable,
            -- consistency = favorable / total (where direction is known)
            CASE
                WHEN COUNT(DISTINCT CASE WHEN ae.effect_direction IN ('favorable','neutral','unfavorable','mixed')
                     THEN ael.canonical_id END) > 0
                THEN ROUND(
                    1.0 * COUNT(DISTINCT CASE WHEN ae.effect_direction = 'favorable' THEN ael.canonical_id END)
                    / COUNT(DISTINCT CASE WHEN ae.effect_direction IN ('favorable','neutral','unfavorable','mixed')
                      THEN ael.canonical_id END),
                    3)
                ELSE 0.0
            END as consistency_score,
            -- weighted_score: n_favorable * avg_confidence
            ROUND(
                COUNT(DISTINCT CASE WHEN ae.effect_direction = 'favorable' THEN ael.canonical_id END)
                * AVG(ael.confidence),
                3) as weighted_score,
            CURRENT_TIMESTAMP
        FROM article_entity_links ael
        LEFT JOIN article_extractions ae ON ael.canonical_id = ae.canonical_id
        WHERE ael.role = 'intervention'
        GROUP BY ael.entity_id
        HAVING n_studies >= 1
    """)
    conn.commit()

    # Report top signals
    rows = conn.execute("""
        SELECT e.canonical_name, s.n_studies, s.n_favorable,
               s.consistency_score, s.weighted_score
        FROM intervention_signals s
        JOIN entity e ON s.entity_id = e.entity_id
        WHERE s.n_studies >= 2
        ORDER BY s.weighted_score DESC
        LIMIT 20
    """).fetchall()

    if rows:
        log.info("Top intervention signals (>= 2 studies):")
        log.info("  %-30s  studies  fav  consistency  weighted", "Entity")
        log.info("  " + "-" * 75)
        for r in rows:
            log.info("  %-30s  %5d  %4d  %10.3f  %8.3f", r[0], r[1], r[2], r[3], r[4])
    else:
        log.info("No signals with >= 2 studies yet. Need more article_extractions.")


# ===================================================================
# CLI
# ===================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PCOS Entity Normalizer -- unify intervention names"
    )
    parser.add_argument(
        "--skip-llm", action="store_true",
        help="Run only layers 1-2 (dictionary + fuzzy). Fast, no Ollama needed.",
    )
    parser.add_argument(
        "--seed-only", action="store_true",
        help="Only seed the entity table from the dictionary. Instant.",
    )
    parser.add_argument(
        "--reset-new-entities", action="store_true",
        help=(
            "Delete all 'new_entity' links and their orphan entities, then re-run "
            "layer 3 with the improved prompt. Use after updating NOISE_TERMS or SEED."
        ),
    )
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    # Step 1: Create tables
    init_db(conn)

    # Optional: reset new_entity links so layer 3 re-evaluates them
    if args.reset_new_entities:
        n_links = conn.execute(
            "SELECT COUNT(*) FROM article_entity_links WHERE method='new_entity'"
        ).fetchone()[0]
        # Find orphan entities: only referenced by new_entity links, not in SEED
        seed_names = set(k.lower() for k in SEED.keys())
        orphan_ids = [
            row[0] for row in conn.execute("""
                SELECT e.entity_id FROM entity e
                LEFT JOIN article_entity_links lnk
                    ON lnk.entity_id = e.entity_id AND lnk.method != 'new_entity'
                WHERE lnk.entity_id IS NULL
            """).fetchall()
            if conn.execute(
                "SELECT canonical_name FROM entity WHERE entity_id=?", (row[0],)
            ).fetchone()[0].lower() not in seed_names
        ]
        if orphan_ids:
            placeholders = ",".join("?" * len(orphan_ids))
            conn.execute(f"DELETE FROM entity WHERE entity_id IN ({placeholders})", orphan_ids)
        conn.execute("DELETE FROM article_entity_links WHERE method='new_entity'")
        conn.commit()
        log.info("Reset: deleted %d new_entity links and %d orphan entities. Re-running layer 3...",
                 n_links, len(orphan_ids))

    # Step 2: Seed entities
    name_to_id = seed_entities(conn)

    if args.seed_only:
        log.info("Done (seed-only mode).")
        conn.close()
        return

    # Step 3: Extract raw terms from DB
    trial_terms = extract_terms_from_trials(conn)
    extraction_terms = extract_terms_from_extractions(conn)
    all_terms = trial_terms + extraction_terms
    log.info("Extracted %d terms (%d from trials, %d from extractions)",
             len(all_terms), len(trial_terms), len(extraction_terms))

    # Step 4: Process through pipeline
    stats = process_terms(conn, all_terms, name_to_id, use_llm=not args.skip_llm)

    # Step 5: Compute signals
    compute_signals(conn)

    # Summary
    log.info("="*60)
    log.info("ENTITY NORMALIZER COMPLETE")
    log.info("  Total terms processed:    %d", stats["total"])
    log.info("  Exact matches:            %d", stats["exact"])
    log.info("  Fuzzy (high conf):        %d", stats["fuzzy"])
    log.info("  Fuzzy verified by LLM:    %d", stats["fuzzy_verified"])
    log.info("  Fuzzy rejected by LLM:    %d", stats["fuzzy_rejected"])
    log.info("  LLM matches (unknowns):   %d", stats["llm"])
    log.info("  Noise filtered:           %d", stats["noise"])
    log.info("  New/unknown entities:     %d", stats["unknown"])
    n_entities = conn.execute("SELECT COUNT(*) FROM entity").fetchone()[0]
    n_links = conn.execute("SELECT COUNT(*) FROM article_entity_links").fetchone()[0]
    log.info("  Entities in DB:        %d", n_entities)
    log.info("  Article-entity links:  %d", n_links)
    log.info("="*60)

    conn.close()


if __name__ == "__main__":
    main()
