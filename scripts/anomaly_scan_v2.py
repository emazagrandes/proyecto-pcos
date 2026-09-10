"""Statistical signal detection across PCOS articles — finds cross-indication drugs, subpopulation effects, unexpected outcomes, and rare consistent findings."""

from __future__ import annotations

import argparse
import json
import logging
import math
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PCOS_PRIMARY_DRUGS = {
    "metformin", "letrozole", "clomiphene citrate", "spironolactone",
    "oral contraceptives", "flutamide", "finasteride",
    "myo-inositol", "d-chiro-inositol", "inositol",
    "berberine",
    "curcumin",
    "melatonin",
    "vitamin d",
    "omega-3",
    "probiotics",
    "gnrh agonists", "gnrh antagonists", "gonadotropins", "hcg", "progesterone",
    "exercise", "lifestyle intervention", "dietary intervention",
    "weight loss", "acupuncture", "laparoscopic ovarian drilling",
    "ivf", "icsi", "ivm", "bariatric surgery",
    "frozen embryo transfer", "fresh embryo transfer",
    "letrozole combined with gonadotropins",
}

# Rarity score helper

def _rarity_factor(n_studies: int) -> float:
    """
    Inverse-log factor: rare interventions score higher.
    n_studies=1  → 1.44  (log2(2)=1)
    n_studies=3  → 0.50  (log2(4)=2)
    n_studies=10 → 0.29
    n_studies=50 → 0.17
    n_studies=200→ 0.13
    This is NOT a penalty for size — it is a bonus for rarity.
    The idea: metformin in 200 studies is established knowledge.
    Something in 3 studies is an unexplored territory worth investigating.
    """
    return round(1.0 / math.log2(n_studies + 2), 3)


# _extract_subpop_from_text removed: population_* structured fields are now
# filled by the extractor (run_ollama_extraction.py with schema-1.1-pop-v2 prompt).
# The anomaly scan uses those fields directly — no regex fallback needed.


# HELPERS

def _load_entity_signals(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load intervention_signals joined with entity names."""
    try:
        return pd.read_sql_query("""
            SELECT
                s.entity_id, e.canonical_name, e.entity_type,
                s.n_studies, s.n_favorable, s.consistency_score, s.weighted_score
            FROM intervention_signals s
            JOIN entity e ON e.entity_id = s.entity_id
            WHERE s.n_studies >= 1
            ORDER BY s.n_favorable DESC, s.consistency_score DESC
        """, conn)
    except Exception as exc:
        log.warning("Could not load intervention_signals: %s", exc)
        return pd.DataFrame()


def _load_extractions(conn: sqlite3.Connection, max_year: int | None = None) -> pd.DataFrame:
    """Load article_extractions (v1.1 schema where available)."""
    try:
        year_filter = f"AND a.year <= {max_year}" if max_year is not None else ""
        return pd.read_sql_query(f"""
            SELECT
                ae.canonical_id, ae.intervention, ae.comparator,
                ae.effect_direction, ae.main_outcomes,
                ae.population, ae.population_diet, ae.population_bmi,
                ae.population_age_range, ae.population_comorbidities,
                ae.population_ethnicity, ae.n_total,
                a.title, a.year, a.study_type, a.evidence_tier,
                l.study_type_llm, l.evidence_tier_llm
            FROM article_extractions ae
            JOIN articles a ON a.canonical_id = ae.canonical_id
            LEFT JOIN article_llm_labels l ON l.canonical_id = ae.canonical_id
            WHERE ae.extraction_status = 'ollama_generated'
              AND ae.intervention IS NOT NULL
              AND ae.intervention != ''
              {year_filter}
        """, conn)
    except Exception as exc:
        log.warning("Could not load article_extractions: %s", exc)
        return pd.DataFrame()


def _load_entity_links(conn: sqlite3.Connection, max_year: int | None = None) -> pd.DataFrame:
    """Load article_entity_links with effect_direction from extractions."""
    try:
        year_filter = f"AND a.year <= {max_year}" if max_year is not None else ""
        return pd.read_sql_query(f"""
            SELECT
                lnk.canonical_id, lnk.entity_id, lnk.role,
                lnk.confidence, lnk.method, lnk.raw_term,
                e.canonical_name, e.entity_type,
                ae.effect_direction, ae.main_outcomes, ae.n_total,
                ae.population_diet, ae.population_bmi, ae.population_ethnicity,
                a.year, a.study_type
            FROM article_entity_links lnk
            JOIN entity e ON e.entity_id = lnk.entity_id
            LEFT JOIN article_extractions ae ON ae.canonical_id = lnk.canonical_id
              AND ae.extraction_status = 'ollama_generated'
            LEFT JOIN articles a ON a.canonical_id = lnk.canonical_id
            WHERE lnk.role = 'intervention'
              {year_filter}
        """, conn)
    except Exception as exc:
        log.warning("Could not load entity links: %s", exc)
        return pd.DataFrame()


def _parse_outcomes(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(o).lower().strip() for o in raw if str(o).strip()]
    text = str(raw).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(o).lower().strip() for o in parsed if str(o).strip()]
        except json.JSONDecodeError:
            pass
    return [text.lower().strip()] if text else []


# TIPO 1 — Cross-indication signal

def detect_tipo1(links_df: pd.DataFrame, min_favorable: int = 2) -> list[dict]:
    """
    Cross-indication signals: interventions NOT in the primary PCOS drug list
    that appear with effect_direction='favorable' in >= min_favorable studies.

    Scoring uses rarity-adjusted curiosity_score:
      score = n_favorable * consistency * (1 + rarity_factor(n_studies))

    This means 2 favorable in 3 studies scores HIGHER than 5 favorable in 200.
    The goal is to surface unknown/repurposed drugs, not rank known PCOS drugs.
    """
    if links_df.empty:
        return []

    signals = []
    for entity_name, group in links_df.groupby("canonical_name"):
        if entity_name.lower() in PCOS_PRIMARY_DRUGS:
            continue

        unique_studies = group.drop_duplicates(subset="canonical_id")
        n_total_studies = len(unique_studies)
        n_favorable = int((unique_studies["effect_direction"] == "favorable").sum())
        n_mixed = int((unique_studies["effect_direction"] == "mixed").sum())
        n_unfavorable = int((unique_studies["effect_direction"] == "unfavorable").sum())
        n_neutral = int((unique_studies["effect_direction"] == "neutral").sum())
        # Studies with known direction (excludes NCT trials without results yet)
        n_with_direction = n_favorable + n_mixed + n_unfavorable + n_neutral

        if n_favorable < min_favorable:
            continue

        articles = unique_studies[["canonical_id", "year", "study_type",
                                    "effect_direction", "main_outcomes"]].to_dict("records")

        # Consistency = favorable / studies-with-results (NOT total including no-result NCTs)
        # Rationale: an intervention being actively studied in 30 trials shouldn't be
        # penalized for lacking results from those ongoing trials.
        consistency = n_favorable / max(n_with_direction, 1)
        rarity = _rarity_factor(n_total_studies)
        curiosity = round(n_favorable * consistency * (1.0 + rarity), 3)

        signal = {
            "type": "tipo1_cross_indication",
            "entity": entity_name,
            "n_studies": n_total_studies,
            "n_with_direction": n_with_direction,
            "n_favorable": n_favorable,
            "n_unfavorable": n_unfavorable,
            "n_mixed": n_mixed,
            "consistency": round(consistency, 2),
            "rarity_factor": rarity,
            "articles": articles[:10],
            "curiosity_score": curiosity,
        }
        signals.append(signal)

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 2 — Biomarker variance by subpopulation

def detect_tipo2(links_df: pd.DataFrame, min_per_group: int = 2) -> list[dict]:
    """
    Subpopulation effect heterogeneity: same intervention shows very different
    favorable rates across subgroups (diet, BMI, ethnicity, comorbidities).

    Uses structured population_* fields from article_extractions directly.
    Run `run_ollama_extraction.py --repopulate-pop-fields` first to ensure
    these fields are filled (requires improved prompt schema-1.1-pop-v2).

    Signal threshold: >= 30pp difference in favorable rate between subgroups.
    """
    if links_df.empty:
        return []

    all_subpop_cols = ["population_diet", "population_bmi",
                       "population_ethnicity", "population_comorbidities"]
    available_cols = [c for c in all_subpop_cols if c in links_df.columns]
    enriched = links_df.copy()

    signals = []
    for entity_name, group in enriched.groupby("canonical_name"):
        subpop_data = group.dropna(subset=available_cols, how="all")
        if len(subpop_data) < min_per_group * 2:
            continue

        for col in available_cols:
            if col not in subpop_data.columns:
                continue
            col_data = subpop_data[
                subpop_data[col].notna() &
                ~subpop_data[col].astype(str).str.lower().isin(("none", "null", "", "[]"))
            ]
            if len(col_data) < min_per_group:
                continue

            sub_summary = []
            for subpop_val, sub_group in col_data.groupby(col):
                if not str(subpop_val).strip():
                    continue
                n = len(sub_group)
                n_fav = int((sub_group["effect_direction"] == "favorable").sum())
                if n >= min_per_group:
                    sub_summary.append({
                        "subpop": str(subpop_val),
                        "n": n,
                        "n_favorable": n_fav,
                        "fav_rate": round(n_fav / n, 2),
                    })

            if len(sub_summary) < 2:
                continue

            rates = [s["fav_rate"] for s in sub_summary]
            rate_range = max(rates) - min(rates)
            if rate_range < 0.30:
                continue

            best = max(sub_summary, key=lambda x: x["fav_rate"])
            worst = min(sub_summary, key=lambda x: x["fav_rate"])
            total_n = sum(s["n"] for s in sub_summary)

            signals.append({
                "type": "tipo2_subpop_variance",
                "entity": entity_name,
                "dimension": col.replace("population_", ""),
                "best_subgroup": best,
                "worst_subgroup": worst,
                "rate_range": round(rate_range, 2),
                "all_subgroups": sub_summary,
                # Score: large range * large n = actionable finding
                "curiosity_score": round(rate_range * math.log2(total_n + 2), 3),
            })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 2b — Cross-intervention subpopulation modifier

def detect_tipo2b_cross_intervention(
    extractions_df: pd.DataFrame,
    baseline_fav_rate: float,
    min_studies: int = 3,
    min_delta: float = 0.15,
) -> list[dict]:
    """
    The "hidden variable detector": finds population characteristics that predict
    favorable PCOS outcomes ACROSS DIFFERENT INTERVENTIONS.

    Unlike Tipo 2 (which looks within one intervention), Tipo 2b looks across ALL
    interventions simultaneously. If women with plant-based diets consistently do
    better across berberine, inositol, and omega-3 studies, the DIET (not any single
    drug) is the signal.

    This is the most under-studied signal type in PCOS research: every RCT controls
    for the intervention but treats population characteristics as background noise.

    Signal threshold:
    - Subgroup favorable_rate >= baseline + min_delta (default +15pp)
    - At least min_studies studies in that subgroup
    - Those studies span at least 2 different interventions (rules out single-drug confound)
    """
    if extractions_df.empty:
        return []

    pop_cols = [
        "population_diet", "population_bmi",
        "population_ethnicity", "population_comorbidities",
    ]
    available = [c for c in pop_cols if c in extractions_df.columns]

    signals = []
    df = extractions_df[
        extractions_df["effect_direction"].notna() &
        extractions_df["effect_direction"].isin(["favorable", "neutral", "unfavorable"])
    ].copy()

    if df.empty:
        return []

    for col in available:
        col_data = df[
            df[col].notna() &
            ~df[col].astype(str).str.lower().isin(("none", "null", "", "[]", "unknown"))
        ]
        if col_data.empty:
            continue

        for val, group in col_data.groupby(col):
            val_str = str(val).strip()
            if not val_str or len(val_str) < 3:
                continue

            # Skip tautological comorbidities: PCOS listed as its own comorbidity
            if col == "population_comorbidities":
                val_lower = val_str.lower()
                if any(t in val_lower for t in (
                    "pcos", "polycystic", "ovary", "ovarian syndrome", "sop"
                )):
                    continue

            n = len(group)
            if n < min_studies:
                continue

            n_fav = int((group["effect_direction"] == "favorable").sum())
            fav_rate = n_fav / n
            delta = fav_rate - baseline_fav_rate

            if delta < min_delta:
                continue

            # Must span at least 2 distinct interventions
            interventions = group["intervention"].dropna().unique().tolist()
            if len(interventions) < 2:
                continue

            canonical_ids = group["canonical_id"].dropna().tolist()
            years = sorted(group["year"].dropna().astype(str).tolist())

            signals.append({
                "type": "tipo2b_cross_intervention_modifier",
                "dimension": col.replace("population_", ""),
                "modifier_value": val_str,
                "n_studies": n,
                "n_favorable": n_fav,
                "favorable_rate": round(fav_rate, 3),
                "baseline_rate": round(baseline_fav_rate, 3),
                "delta_vs_baseline": round(delta, 3),
                "n_distinct_interventions": len(interventions),
                "sample_interventions": interventions[:6],
                "canonical_ids": canonical_ids[:10],
                "year_range": f"{years[0]}–{years[-1]}" if years else "",
                "anomaly_reason": (
                    f"{val_str} subgroup: {fav_rate:.0%} favorable "
                    f"(+{delta:.0%} vs baseline) across {len(interventions)} different interventions. "
                    f"The diet/population factor, not the drug, may be the real driver."
                ),
                # Higher score for: larger delta, more interventions, more studies
                "curiosity_score": round(
                    delta * math.log2(n + 2) * math.log2(len(interventions) + 2), 3
                ),
            })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 3 — Unexpected outcome co-occurrence

EXPECTED_PCOS_OUTCOMES = {
    "menstrual regularity", "ovulation", "testosterone", "amh",
    "insulin resistance", "homa-ir", "bmi", "weight", "lh", "fsh",
    "pregnancy rate", "hirsutism", "acne", "androstenedione", "shbg",
    "glucose", "lipid profile", "quality of life",
    "clinical pregnancy", "live birth", "cycle regulation",
}


def detect_tipo3(links_df: pd.DataFrame, min_co_occurrence: int = 2) -> list[dict]:
    """
    For each intervention, find outcomes that appear ≥min_co_occurrence times
    but are NOT in the expected PCOS outcome set.

    These are unexpected co-occurring outcomes that may hint at novel mechanisms.
    """
    if links_df.empty:
        return []

    signals = []
    for entity_name, group in links_df.groupby("canonical_name"):
        outcome_counter: Counter = Counter()
        for _, row in group.iterrows():
            outcomes = _parse_outcomes(row.get("main_outcomes"))
            for outcome in outcomes:
                # Filter: not expected
                is_expected = any(
                    exp in outcome or outcome in exp
                    for exp in EXPECTED_PCOS_OUTCOMES
                )
                if not is_expected and len(outcome) > 5:
                    outcome_counter[outcome] += 1

        unexpected = [
            {"outcome": out, "n_studies": count}
            for out, count in outcome_counter.most_common(10)
            if count >= min_co_occurrence
        ]

        if not unexpected:
            continue

        n_total = len(group["canonical_id"].unique())
        signals.append({
            "type": "tipo3_unexpected_outcome",
            "entity": entity_name,
            "n_studies_total": n_total,
            "unexpected_outcomes": unexpected,
            "curiosity_score": round(sum(u["n_studies"] for u in unexpected) / max(n_total, 1), 2),
        })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 4 — Hidden gems: rare but consistent

def detect_tipo4_hidden_gems(
    links_df: pd.DataFrame,
    max_studies: int = 5,
    min_favorable_rate: float = 0.75,
) -> list[dict]:
    """
    The most important detector for our purposes.

    Finds interventions that appear in very few studies (1 to max_studies)
    but have high or perfect favorable consistency. These are the cases
    where:
      - One or two labs found something promising
      - Nobody in mainstream literature aggregated it
      - It's exactly what a human researcher would miss but our system catches

    Excludes known primary PCOS drugs (those have been studied enough).
    Includes both favorable and mixed (partial credit for mixed = 0.5).

    Score = favorable_rate * rarity_factor * log2(mean_sample_size + 2)
      - favorable_rate: how consistently positive
      - rarity_factor: bonus for being obscure
      - sample_size weight: a n=50 RCT is more credible than n=5 pilot
    """
    if links_df.empty:
        return []

    signals = []
    for entity_name, group in links_df.groupby("canonical_name"):
        if entity_name.lower() in PCOS_PRIMARY_DRUGS:
            continue

        unique_studies = group.drop_duplicates(subset="canonical_id")
        n_studies = len(unique_studies)

        if n_studies > max_studies:
            continue

        # Count effect directions
        n_favorable = int((unique_studies["effect_direction"] == "favorable").sum())
        n_mixed = int((unique_studies["effect_direction"] == "mixed").sum())
        n_unfavorable = int((unique_studies["effect_direction"] == "unfavorable").sum())
        n_with_direction = n_favorable + n_mixed + n_unfavorable

        if n_with_direction == 0:
            continue  # no effect_direction data at all

        # Partial credit: mixed = 0.5, favorable = 1.0
        weighted_positive = n_favorable + 0.5 * n_mixed
        favorable_rate = weighted_positive / n_with_direction

        if favorable_rate < min_favorable_rate:
            continue

        # Sample size quality factor
        n_total_vals = unique_studies["n_total"].dropna()
        mean_n = float(n_total_vals.mean()) if len(n_total_vals) > 0 else 10.0
        sample_quality = math.log2(mean_n + 2)  # log2(12) ≈ 3.6 for n=10; log2(52) ≈ 5.7 for n=50

        rarity = _rarity_factor(n_studies)
        curiosity = round(favorable_rate * rarity * sample_quality, 3)

        articles = unique_studies[["canonical_id", "year", "study_type",
                                    "effect_direction", "main_outcomes",
                                    "n_total"]].to_dict("records")

        signals.append({
            "type": "tipo4_hidden_gem",
            "entity": entity_name,
            "n_studies": n_studies,
            "n_favorable": n_favorable,
            "n_mixed": n_mixed,
            "n_unfavorable": n_unfavorable,
            "favorable_rate": round(favorable_rate, 2),
            "mean_sample_size": round(mean_n, 0),
            "rarity_factor": rarity,
            "curiosity_score": curiosity,
            "articles": articles[:8],
        })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)

    # DOI-LEVEL DEDUPLICATION
    # Problem: the entity normalizer sometimes creates multiple canonical
    # entities for the same intervention variant (e.g. "nc-fet", "mnc-fet",
    # "pc-fet" all from the same paper DOI 10.1007/s10815-025-03523-4).
    # Each one scores identically and floods the T4 report.
    #
    # Fix: process signals in score order (already sorted).
    # Track every canonical_id (DOI/article) already "claimed" by a higher-
    # scoring signal. If ALL articles of a new signal are already claimed,
    # mark it as a duplicate and skip it. This is conservative — a signal
    # with even ONE novel article passes through.
    seen_canonical_ids: set[str] = set()
    deduped: list[dict] = []
    for sig in signals:
        sig_ids = {a["canonical_id"] for a in sig.get("articles", []) if a.get("canonical_id")}
        if not sig_ids:
            # No articles recorded — keep it (can't deduplicate without IDs)
            deduped.append(sig)
            continue
        if sig_ids.issubset(seen_canonical_ids):
            # Every single article in this signal was already claimed by a
            # higher-scoring signal → this is a duplicate entity name, skip it.
            log.debug("T4 dedup: skipping '%s' (all %d article(s) already in higher-scoring signal)",
                      sig["entity"], len(sig_ids))
            continue
        seen_canonical_ids.update(sig_ids)
        deduped.append(sig)

    return deduped


# TIPO 6 — Temporal Anomaly

def detect_tipo6_temporal(
    links_df: pd.DataFrame,
    year_cutoff: int = 2021,
    min_per_era: int = 2,
    min_delta: float = 0.25,
) -> list[dict]:
    """
    Temporal anomaly: same intervention, very different favorable_rate
    in pre-cutoff vs post-cutoff studies.

    Two patterns:
      "rising"  — recent studies more favorable → converging evidence, worth investigating now
      "falling" — old studies more favorable → non-replication signal, possible publication bias

    Threshold: |delta| >= min_delta (default 25pp), at least min_per_era studies in each era.
    Score = |delta| * log2(n_total + 2) — larger deltas on more studies score higher.
    """
    if links_df.empty:
        return []

    df = links_df[
        links_df["year"].notna() &
        links_df["effect_direction"].isin(["favorable", "neutral", "unfavorable", "mixed"])
    ].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna()]

    if df.empty:
        return []

    signals = []
    for entity_name, group in df.groupby("canonical_name"):
        unique = group.drop_duplicates(subset="canonical_id")

        old = unique[unique["year"] <= year_cutoff]
        recent = unique[unique["year"] > year_cutoff]

        if len(old) < min_per_era or len(recent) < min_per_era:
            continue

        old_fav = (old["effect_direction"] == "favorable").sum() / len(old)
        recent_fav = (recent["effect_direction"] == "favorable").sum() / len(recent)
        delta = recent_fav - old_fav

        if abs(delta) < min_delta:
            continue

        trend = "rising" if delta > 0 else "falling"
        n_total = len(unique)

        signals.append({
            "type": "tipo6_temporal_anomaly",
            "entity": entity_name,
            "trend": trend,
            "year_cutoff": year_cutoff,
            "n_old": int(len(old)),
            "n_recent": int(len(recent)),
            "fav_rate_old": round(float(old_fav), 2),
            "fav_rate_recent": round(float(recent_fav), 2),
            "delta": round(float(delta), 2),
            "anomaly_reason": (
                f"{'Converging evidence' if trend == 'rising' else 'Non-replication signal'}: "
                f"favorable rate {'increased' if trend == 'rising' else 'decreased'} "
                f"from {old_fav:.0%} (pre-{year_cutoff + 1}, n={len(old)}) "
                f"to {recent_fav:.0%} (post-{year_cutoff}, n={len(recent)}). "
                f"{'Recent trials confirm benefit — timing is good to investigate.' if trend == 'rising' else 'Early enthusiasm may not replicate in larger/newer trials.'}"
            ),
            "curiosity_score": round(abs(float(delta)) * math.log2(n_total + 2), 3),
        })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 7 — Contradiction Analysis

def detect_tipo7_contradictions(
    links_df: pd.DataFrame,
    min_each: int = 1,
) -> list[dict]:
    """
    Same intervention, studies with BOTH favorable AND unfavorable effect_direction.

    The detector tries to find what differentiates the two groups:
      - population_bmi: obese favorable, lean unfavorable → insulin-resistance hypothesis
      - population_ethnicity: different metabolic baselines
      - study_type: RCT vs cohort → methodological confound
      - year: older favorable, newer unfavorable → non-replication (complementary to Tipo 6)

    A differentiator is reported when favorable and unfavorable groups have
    DISJOINT values for a field (no overlap). This is a conservative criterion
    that surfaces only the strongest structural splits.

    Score = (n_unfavorable / n_total) * log2(n_total + 2)
      Penalizes contradictions in very small bodies of evidence.
      Rewards contradictions in larger, better-studied interventions.
    """
    if links_df.empty:
        return []

    NOISE_VALS = {"none", "null", "", "nan", "unknown", "unclear", "mixed bmi"}
    signals = []

    for entity_name, group in links_df.groupby("canonical_name"):
        unique = group.drop_duplicates(subset="canonical_id")

        favorable = unique[unique["effect_direction"] == "favorable"]
        unfavorable = unique[unique["effect_direction"] == "unfavorable"]

        if len(favorable) < min_each or len(unfavorable) < min_each:
            continue

        n_total = len(unique)
        differentiators = []

        # --- Check categorical fields ---
        for col in ["population_bmi", "population_ethnicity", "study_type"]:
            if col not in unique.columns:
                continue

            def _clean_vals(df_slice: pd.DataFrame) -> set:
                return {
                    str(v).lower().strip()
                    for v in df_slice[col].dropna()
                    if str(v).lower().strip() not in NOISE_VALS
                }

            fav_vals = _clean_vals(favorable)
            unfav_vals = _clean_vals(unfavorable)

            if fav_vals and unfav_vals and not fav_vals.intersection(unfav_vals):
                differentiators.append({
                    "field": col.replace("population_", ""),
                    "in_favorable": sorted(fav_vals)[:3],
                    "in_unfavorable": sorted(unfav_vals)[:3],
                    "strength": "strong (no overlap)",
                })

        # --- Check year ---
        if "year" in unique.columns:
            fav_years = pd.to_numeric(favorable["year"], errors="coerce").dropna()
            unfav_years = pd.to_numeric(unfavorable["year"], errors="coerce").dropna()
            if len(fav_years) > 0 and len(unfav_years) > 0:
                year_delta = float(fav_years.mean() - unfav_years.mean())
                if abs(year_delta) >= 3:
                    differentiators.append({
                        "field": "year",
                        "in_favorable": f"mean {fav_years.mean():.0f}",
                        "in_unfavorable": f"mean {unfav_years.mean():.0f}",
                        "strength": f"mean diff {year_delta:+.1f} years",
                    })

        top_diff = differentiators[0] if differentiators else None
        signals.append({
            "type": "tipo7_contradiction",
            "entity": entity_name,
            "n_favorable": int(len(favorable)),
            "n_unfavorable": int(len(unfavorable)),
            "n_total": int(n_total),
            "n_differentiators_found": len(differentiators),
            "top_differentiator": top_diff,
            "all_differentiators": differentiators,
            "anomaly_reason": (
                f"{len(favorable)} favorable vs {len(unfavorable)} unfavorable studies. "
                + (
                    f"Strongest differentiator: {top_diff['field']} "
                    f"(favorable={top_diff['in_favorable']}, "
                    f"unfavorable={top_diff['in_unfavorable']})."
                    if top_diff else
                    "No clear structural differentiator found — could be methodological noise."
                )
            ),
            "curiosity_score": round(
                (len(unfavorable) / n_total) * math.log2(n_total + 2), 3
            ),
        })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 9 — Secondary Biomarker Movement (Pleiotropic Signals)

# Secondary biomarker categories — outcomes that are NOT primary PCOS endpoints
# but belong to recognized clinical domains. Grouped to avoid single-keyword noise.
SECONDARY_BIOMARKER_CATEGORIES: dict[str, list[str]] = {
    "cardiovascular": [
        "blood pressure", "hdl", "ldl", "triglyceride", "cholesterol",
        "cardiovascular", "hs-crp", "crp", "homocysteine", "fibrinogen",
        "carotid", "endothelial", "flow-mediated", "arterial stiffness",
    ],
    "inflammation": [
        "il-6", "il-1", "tnf-alpha", "tnf", "interleukin", "inflammatory",
        "inflammation", "oxidative stress", "mda", "sod", "catalase",
        "glutathione", "myeloperoxidase", "8-ohdg", "nitric oxide",
    ],
    "gut_microbiome": [
        "microbiome", "gut flora", "lactobacillus", "bifidobacterium",
        "intestinal permeability", "fecal", "short-chain fatty acid",
        "butyrate", "dysbiosis", "akkermansia",
    ],
    "mental_health": [
        "depression", "anxiety", "mood", "quality of life", "psychological",
        "stress", "cortisol", "sleep", "fatigue", "cognitive", "well-being",
    ],
    "thyroid": [
        "tsh", "free t3", "free t4", "thyroid peroxidase", "thyroid antibody",
        "hypothyroidism", "hashimoto",
    ],
    "bone_density": [
        "bone mineral density", "osteocalcin", "calcium", "alkaline phosphatase",
        "parathyroid", "vitamin d", "bone turnover",
    ],
    "liver": [
        "alt", "ast", "ggt", "nafld", "hepatic steatosis", "liver enzyme",
        "hepatic fat", "liver fibrosis",
    ],
}


def _classify_secondary_biomarker(outcome: str) -> str | None:
    """Returns category name if outcome matches a secondary biomarker category, else None."""
    for category, keywords in SECONDARY_BIOMARKER_CATEGORIES.items():
        if any(kw in outcome for kw in keywords):
            return category
    return None


def detect_tipo9_secondary_biomarkers(
    links_df: pd.DataFrame,
    min_co_occurrence: int = 2,
) -> list[dict]:
    """
    Pleiotropic signals: secondary biomarker categories that appear consistently
    in FAVORABLE studies of an intervention — beyond primary PCOS endpoints.

    Key difference from Tipo 3:
      - Tipo 3: ANY study, counts raw unexpected outcomes as keywords
      - Tipo 9: FAVORABLE studies only, groups into clinical categories,
                requires min_co_occurrence hits in the same category

    High-value signal: "metformin favorably affects NAFLD markers in 4 favorable
    PCOS studies" → pleiotropic benefit relevant for the PCOS+metabolic phenotype.

    Score = sum(category_hits) / n_favorable_studies
      Normalized by study count: signals that appear in most favorable studies
      score higher than those that appear in just one.
    """
    if links_df.empty:
        return []

    favorable_df = links_df[links_df["effect_direction"] == "favorable"]
    if favorable_df.empty:
        return []

    signals = []
    for entity_name, group in favorable_df.groupby("canonical_name"):
        category_counter: Counter = Counter()
        category_outcomes: dict[str, list[str]] = defaultdict(list)

        for _, row in group.iterrows():
            outcomes = _parse_outcomes(row.get("main_outcomes"))
            for outcome in outcomes:
                # Skip primary PCOS outcomes
                is_primary = any(
                    exp in outcome or outcome in exp
                    for exp in EXPECTED_PCOS_OUTCOMES
                )
                if is_primary:
                    continue
                cat = _classify_secondary_biomarker(outcome)
                if cat:
                    category_counter[cat] += 1
                    if outcome not in category_outcomes[cat]:
                        category_outcomes[cat].append(outcome)

        if not category_counter:
            continue

        n_favorable_studies = int(group["canonical_id"].nunique())
        secondary_signals = [
            {
                "category": cat,
                "n_hits": count,
                "example_outcomes": category_outcomes[cat][:3],
            }
            for cat, count in category_counter.most_common()
            if count >= min_co_occurrence
        ]

        if not secondary_signals:
            continue

        top = secondary_signals[0]
        signals.append({
            "type": "tipo9_secondary_biomarker",
            "entity": entity_name,
            "n_favorable_studies": n_favorable_studies,
            "secondary_signals": secondary_signals,
            "top_category": top["category"],
            "anomaly_reason": (
                f"In {n_favorable_studies} favorable studies, {entity_name} "
                f"consistently affects {top['category']} markers "
                f"({', '.join(top['example_outcomes'][:2])}) "
                f"alongside primary PCOS endpoints — pleiotropic benefit signal."
            ),
            "curiosity_score": round(
                sum(s["n_hits"] for s in secondary_signals) / max(n_favorable_studies, 1), 2
            ),
        })

    signals.sort(key=lambda x: x["curiosity_score"], reverse=True)
    return signals


# TIPO 8 — KG Convergence (hipótesis mecanísticas emergentes)

# Palabras clave que indican un nodo PCOS-relevante (los "C" del path A→B→C)
# Un nodo es "endpoint PCOS" si su nombre contiene alguna de estas keywords.
PCOS_ENDPOINT_KW = {
    "testosterone", "androgen", "hyperandrogenism", "lh", "fsh", "amh",
    "dhea", "progesterone", "estradiol", "shbg", "prolactin",
    "insulin", "homa", "glucose", "glycem", "sensitiv",
    "ovulat", "follicle", "fertilit", "pregnan", "menstrual", "menstruation",
    "ovarian", "pcos", "polycystic", "cycle regularity",
    "weight", "bmi", "obesity", "adipos",
    "inflammation", "nf-kb", "nfkb", "tnf", "interleukin", "il-6", "crp",
    "oxidative stress", "reactive oxygen", "antioxidant",
    "androstenedione", "hirsutism", "acne",
    "depression", "anxiety", "quality of life",
}

# Nodos "genéricos" que como intermediario (B) no añaden información:
# si el camino pasa por "pcos" como B, el link no es mecanístico sino tautológico.
GENERIC_NODES = {
    "pcos", "polycystic ovary syndrome", "women with pcos",
    "pcos patients", "pcos group", "control", "placebo",
}


def _is_pcos_relevant(node: str) -> bool:
    """True si el nodo es un endpoint relevante para PCOS."""
    n = node.lower()
    return any(kw in n for kw in PCOS_ENDPOINT_KW)


def _is_generic(node: str) -> bool:
    """True si el nodo es demasiado genérico para ser un intermediario útil."""
    return node.lower().strip() in GENERIC_NODES


def detect_tipo8_kg_convergence(
    conn: sqlite3.Connection,
    min_papers_per_edge: int = 2,
    min_score: float = 1.5,
    top_n: int = 20,
) -> list[dict]:
    """
    KG Convergence — hipótesis mecanísticas de dos saltos.

    El grafo de mecanismos (mechanism_links) contiene triples del tipo:
        source_name --[relation_type]--> target_name

    Cada triple viene de UN artículo. Cuando el MISMO triple aparece en
    N artículos independientes, esa conexión está "confirmada" por convergencia.

    Este detector busca CAMINOS DE DOS SALTOS donde AMBOS saltos están
    confirmados por ≥ min_papers_per_edge artículos:

        A --[r1]--> B --[r2]--> C

    donde:
        A = intervención (drug/supplement/procedure)
        B = mecanismo intermedio (NF-kB, AMPK, oxidative stress, ...)
        C = endpoint relevante para PCOS

    El valor científico: ningún paper individual dice "A afecta C vía B".
    Cada paper dice una cosa: paper 1 reporta A→B, paper 2 reporta B→C.
    El sistema conecta esos hallazgos independientes y genera la hipótesis
    mecanística emergente.

    Scoring:
        convergence_score = n_papers_hop1 × n_papers_hop2 × avg_confidence

    Un score de 4.0 significa: 2 papers confirman hop1 y 2 papers confirman
    hop2, con confianza promedio de 1.0 — es la señal mínima interesante.
    Un score de 9.0 significa: 3×3 con confianza 1.0 — señal fuerte.
    """
    try:
        rows = conn.execute("""
            SELECT source_name, relation_type, target_name,
                   confidence, canonical_id
            FROM mechanism_links
            WHERE source_name IS NOT NULL
              AND target_name IS NOT NULL
              AND confidence >= 0.5
        """).fetchall()
    except Exception as exc:
        log.warning("detect_tipo8: could not load mechanism_links: %s", exc)
        return []

    if not rows:
        log.info("detect_tipo8: mechanism_links is empty — skipping")
        return []

    # PASO 1: Construir el grafo de aristas CONFIRMADAS
    # Agrupamos por (source_norm, relation, target_norm) y contamos
    # cuántos artículos independientes reportan ese triple.
    #
    # "norm" = lowercase + strip, para unificar variantes tipográficas.
    # No es normalización perfecta pero captura el 80% de duplicados.
    #
    # edge_data[(A, rel, B)] = {
    #     "n_papers": int,
    #     "avg_confidence": float,
    #     "papers": [canonical_id, ...]
    # }

    from collections import defaultdict

    edge_raw: dict[tuple, list] = defaultdict(list)

    for source, rel, target, conf, cid in rows:
        key = (source.lower().strip(), rel.lower().strip(), target.lower().strip())
        edge_raw[key].append((conf, cid))

    # Filtrar: solo aristas con ≥ min_papers_per_edge artículos
    confirmed_edges: dict[tuple, dict] = {}
    for (src, rel, tgt), entries in edge_raw.items():
        # Deduplicate by canonical_id (same paper shouldn't count twice)
        seen_cids: dict[str, float] = {}
        for conf, cid in entries:
            if cid not in seen_cids or conf > seen_cids[cid]:
                seen_cids[cid] = conf

        n_papers = len(seen_cids)
        if n_papers < min_papers_per_edge:
            continue

        avg_conf = sum(seen_cids.values()) / n_papers
        confirmed_edges[(src, rel, tgt)] = {
            "n_papers": n_papers,
            "avg_confidence": round(avg_conf, 3),
            "papers": list(seen_cids.keys()),
        }

    log.info("detect_tipo8: %d confirmed edges (≥%d papers each)",
             len(confirmed_edges), min_papers_per_edge)

    if not confirmed_edges:
        return []

    # PASO 2: Índice de salida por nodo fuente
    # Para encontrar caminos A→B→C eficientemente, construimos:
    #   outgoing[node_A] = lista de (rel, node_B, edge_data)
    # así, dado un nodo B de una arista A→B, podemos buscar
    # todas las aristas que salen de B hacia algún C.

    outgoing: dict[str, list[tuple]] = defaultdict(list)
    for (src, rel, tgt), data in confirmed_edges.items():
        outgoing[src].append((rel, tgt, data))

    # PASO 3: Buscar caminos de dos saltos A → B → C
    # Para cada arista confirmada A→B:
    #   Para cada arista confirmada B→C:
    #     Si C es PCOS-relevante y B no es genérico:
    #       Calcular score y guardar el path

    paths: list[dict] = []
    seen_paths: set[tuple] = set()  # evitar duplicados (A, B, C)

    for (src_A, rel1, tgt_B), data1 in confirmed_edges.items():
        if _is_generic(src_A):
            continue  # src_A genérico (ej: "pcos") hace el path tautológico
        if _is_generic(tgt_B):
            continue  # B genérico no aporta mecanismo

        # Buscar todos los C accesibles desde B
        for rel2, tgt_C, data2 in outgoing.get(tgt_B, []):
            if tgt_C == src_A:
                continue  # evitar loops triviales A→B→A
            if not _is_pcos_relevant(tgt_C):
                continue  # C debe ser relevante para PCOS

            path_key = (src_A, tgt_B, tgt_C)
            if path_key in seen_paths:
                continue
            seen_paths.add(path_key)

            # Score = n_papers_hop1 × n_papers_hop2 × promedio de confianzas
            # Esto premia la convergencia (más papers = más robusto)
            # y la calidad (alta confianza en ambos saltos).
            score = (
                data1["n_papers"]
                * data2["n_papers"]
                * (data1["avg_confidence"] + data2["avg_confidence"]) / 2
            )

            if score < min_score:
                continue

            paths.append({
                # El nodo A (fuente): idealmente un fármaco/suplemento
                "drug": src_A,
                # El nodo B (intermediario): el mecanismo biológico
                "mechanism": tgt_B,
                # El nodo C (endpoint): outcome relevante para PCOS
                "endpoint": tgt_C,
                # Relaciones
                "relation_hop1": rel1,
                "relation_hop2": rel2,
                # Evidencia hop 1 (drug → mechanism)
                "n_papers_hop1": data1["n_papers"],
                "avg_conf_hop1": data1["avg_confidence"],
                "papers_hop1": data1["papers"][:3],
                # Evidencia hop 2 (mechanism → endpoint)
                "n_papers_hop2": data2["n_papers"],
                "avg_conf_hop2": data2["avg_confidence"],
                "papers_hop2": data2["papers"][:3],
                # Score final
                "convergence_score": round(score, 3),
                # Hipótesis en lenguaje natural
                "hypothesis": (
                    f"{src_A} {rel1} {tgt_B} "
                    f"({data1['n_papers']} papers), y {tgt_B} {rel2} {tgt_C} "
                    f"({data2['n_papers']} papers) → "
                    f"hipótesis: {src_A} modula {tgt_C} vía {tgt_B}"
                ),
            })

    # Ordenar por score descendente
    paths.sort(key=lambda x: x["convergence_score"], reverse=True)

    log.info("detect_tipo8: %d emergent 2-hop hypotheses (score >= %.1f)",
             len(paths), min_score)

    return paths[:top_n]


# NOVELTY VERIFICATION — búsqueda de evidencia directa pre-síntesis

def _pubmed_search_raw(query: str, max_results: int = 5) -> dict:
    """
    Busca en PubMed via E-utilities (sin API key, límite 3 req/s).
    Devuelve: {n_total, titles: [str], pmids: [str], error: str|None}

    Por qué PubMed y no nuestra DB:
      Nuestra DB cubre ~32% de artículos. PubMed tiene todo.
      Si una hipótesis ya fue estudiada directamente, aparecerá en PubMed
      aunque no esté en nuestras extracciones.
    """
    import time
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    result = {"n_total": 0, "titles": [], "pmids": [], "error": None}

    try:
        # 1. ESearch — obtener PMIDs y total
        encoded_query = urllib.parse.quote(query)
        search_url = (
            f"{base}esearch.fcgi?db=pubmed"
            f"&term={encoded_query}"
            f"&retmax={max_results}"
            f"&sort=relevance"
        )
        with urllib.request.urlopen(search_url, timeout=12) as resp:
            root = ET.fromstring(resp.read())

        result["n_total"] = int(root.findtext("Count", "0"))
        pmids = [el.text for el in root.findall(".//IdList/Id") if el.text]
        result["pmids"] = pmids

        # 2. EFetch — obtener títulos (solo si hay resultados)
        if pmids:
            time.sleep(0.35)  # NCBI rate limit: ≤3 req/s sin API key
            fetch_url = (
                f"{base}efetch.fcgi?db=pubmed"
                f"&id={','.join(pmids[:max_results])}"
                f"&rettype=abstract&retmode=xml"
            )
            with urllib.request.urlopen(fetch_url, timeout=15) as resp:
                fetch_root = ET.fromstring(resp.read())

            for article in fetch_root.findall(".//Article"):
                title = article.findtext("ArticleTitle", "")
                pub_types = [pt.text for pt in article.findall(".//PublicationType") if pt.text]
                year_el = article.find(".//Journal/JournalIssue/PubDate/Year")
                year = year_el.text if year_el is not None else "?"
                # Marcar si es meta-análisis o revisión sistemática
                is_ma = any("Meta-Analysis" in pt or "Systematic Review" in pt
                            for pt in pub_types)
                label = "[META-ANÁLISIS] " if is_ma else ""
                result["titles"].append(f"{label}{title[:120]} ({year})")

    except Exception as exc:
        result["error"] = str(exc)

    return result


def _run_llm(prompt: str, num_predict: int = 800, temperature: float = 0.20) -> str:
    """Llama al backend LLM configurado y devuelve el texto de respuesta."""
    return _llm_generate(prompt, temperature=temperature, max_tokens=num_predict)


def _execute_llm_searches(queries: list) -> str:
    """
    Ejecuta en PubMed las queries que el LLM pidió (Paso 1).

    Acepta tanto list[str] como list[tuple[str,str]] donde la tupla es
    ("BROAD"/"SPECIFIC", "query text"). La arquitectura de 2 capas pasa tuplas
    para que el output etiquete cada búsqueda con su rol (campo vs ángulo específico).

    Por qué el LLM formula las queries (no nosotros):
      - El LLM entiende el matiz semántico de cada hipótesis
      - Sabe qué términos son sinónimos en la literatura biomédica
      - Formula queries que van al corazón de la hipótesis, no a sus componentes por separado
      - Evita el falso positivo de "A y C mencionados en el mismo paper sin relación causal"

    Devuelve un bloque de texto con los resultados para el Paso 2.
    """
    import time as _time

    if not queries:
        return "  (ninguna query ejecutada)"

    lines: list[str] = []
    for item in queries[:12]:  # máx 12 queries (6 hipótesis × 2 capas)
        # Desempaquetar si es tupla (tipo, query) — arquitectura BROAD+SPECIFIC
        if isinstance(item, tuple):
            q_type, q = item  # e.g. ("BROAD", "SGLT2 AND PCOS")
            type_label = f"[{q_type}] "
        else:
            q = item
            type_label = ""
        q = q.strip().strip('"').strip("'")
        if not q:
            continue
        res = _pubmed_search_raw(q, max_results=4)
        _time.sleep(0.4)  # NCBI rate limit

        n = res["n_total"]
        err = res.get("error")

        lines.append(f'\n{type_label}Query: "{q}"')
        if err:
            lines.append(f"  ERROR: {err}")
            continue

        if n == 0:
            lines.append("  --> 0 resultados: esta combinacion NO ha sido estudiada directamente")
        elif n <= 5:
            lines.append(f"  --> {n} resultado(s): muy pocos, posiblemente ninguno aborda la hipotesis central")
        elif n <= 20:
            lines.append(f"  --> {n} resultados: area emergente, revisar si los titulos son relevantes")
        elif n <= 60:
            lines.append(f"  --> {n} resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada")
        else:
            lines.append(f"  --> {n} resultados: campo maduro, alta probabilidad de que ya existe evidencia")

        for t in res.get("titles", [])[:3]:
            lines.append(f"    · {t}")

    return "\n".join(lines) if lines else "  (sin resultados)"


# LLM SYNTHESIS

from llm_client import generate as _llm_generate


def _generate_synthesis(
    tipo1: list[dict],
    tipo2b: list[dict],
    tipo4: list[dict],
    tipo6: list[dict],
    tipo7: list[dict],
    tipo8: list[dict],
    tipo9: list[dict],
    baseline_rate: float = 0.38,
    direct_evidence: str = "",   # ignorado, legacy
) -> tuple[str, str]:
    """
    Síntesis en DOS PASOS con búsqueda PubMed dirigida por el LLM.

    PASO 1 — Gemma analiza señales y decide qué buscar en PubMed.
    PASO 2 — Python ejecuta esas queries, Gemma recibe resultados y sintetiza.

    Retorna: (synthesis_markdown, pubmed_audit_block)
    """
    # ---- Formatters (signal tables → compact text for prompts) ----

    def _fmt_t1(sigs: list[dict], n: int = 8) -> str:
        lines = []
        for s in sigs[:n]:
            n_dir = s.get("n_with_direction", s["n_favorable"])
            lines.append(
                f"  [{s['entity']}] "
                f"{s['n_favorable']}/{n_dir} favorable ({s['consistency']:.0%}) | "
                f"total_in_DB={s['n_studies']} | score={s['curiosity_score']}"
            )
        return "\n".join(lines) if lines else "  (none)"

    def _fmt_t2b(sigs: list[dict], n: int = 6) -> str:
        lines = []
        for s in sigs[:n]:
            lines.append(
                f"  [{s['modifier_value']}] dim={s['dimension']} | "
                f"{s['favorable_rate']:.0%} fav (+{s['delta_vs_baseline']:.0%} vs baseline) | "
                f"n={s['n_studies']} studies, {s['n_distinct_interventions']} interventions | "
                f"sample: {', '.join(s['sample_interventions'][:3])}"
            )
        return "\n".join(lines) if lines else "  (none)"

    def _fmt_t4(sigs: list[dict], n: int = 8) -> str:
        lines = []
        for s in sigs[:n]:
            outs = []
            for art in s.get("articles", [])[:1]:
                outs = _parse_outcomes(art.get("main_outcomes", ""))[:3]
            lines.append(
                f"  [{s['entity']}] {s['n_studies']} study(ies) all favorable | "
                f"mean N={s['mean_sample_size']:.0f} | "
                f"outcomes: {', '.join(outs) or 'n/a'} | score={s['curiosity_score']}"
            )
        return "\n".join(lines) if lines else "  (none)"

    def _fmt_t6(sigs: list[dict]) -> str:
        lines = []
        for s in sigs:
            direction = "RISING" if s["trend"] == "rising" else "FALLING (non-replication)"
            lines.append(
                f"  [{s['entity']}] {direction} | "
                f"{s['fav_rate_old']:.0%} pre-{s['year_cutoff']+1} (n={s['n_old']}) → "
                f"{s['fav_rate_recent']:.0%} post-{s['year_cutoff']} (n={s['n_recent']}) | "
                f"delta={s['delta']:+.0%}"
            )
        return "\n".join(lines) if lines else "  (none)"

    def _fmt_t7(sigs: list[dict], n: int = 5) -> str:
        lines = []
        for s in sigs[:n]:
            diff = s.get("top_differentiator")
            diff_str = (
                f"differentiator: {diff['field']} "
                f"(fav={diff['in_favorable']}, unfav={diff['in_unfavorable']})"
                if diff else "no structural differentiator"
            )
            lines.append(
                f"  [{s['entity']}] {s['n_favorable']} fav vs {s['n_unfavorable']} unfav "
                f"(total {s['n_total']}) | {diff_str}"
            )
        return "\n".join(lines) if lines else "  (none)"

    def _fmt_t8(sigs: list[dict], n: int = 8) -> str:
        lines = []
        for s in sigs[:n]:
            lines.append(
                f"  [{s['drug']} --[{s['relation_hop1']}]--> {s['mechanism']} "
                f"--[{s['relation_hop2']}]--> {s['endpoint']}] "
                f"hop1={s['n_papers_hop1']}p(conf={s['avg_conf_hop1']}) | "
                f"hop2={s['n_papers_hop2']}p(conf={s['avg_conf_hop2']}) | "
                f"score={s['convergence_score']}"
            )
        return "\n".join(lines) if lines else "  (none — KG sparse, growing)"

    def _fmt_t9(sigs: list[dict], n: int = 6) -> str:
        lines = []
        for s in sigs[:n]:
            cats = " | ".join(
                f"{c['category']}:{c['n_hits']}hits"
                for c in s.get("secondary_signals", [])[:3]
            )
            lines.append(
                f"  [{s['entity']}] n_fav_studies={s['n_favorable_studies']} | {cats}"
            )
        return "\n".join(lines) if lines else "  (none)"

    _n_with_dir = sum(s.get("n_with_direction", 0) for s in tipo1)

    # SEÑALES COMPACTAS — bloque compartido por ambos pasos
    signals_block = f"""[T1] Cross-indication (NOT primary PCOS drugs, non-zero favorable results)
{_fmt_t1(tipo1)}

[T2b] Hidden population modifiers (cross-intervention, data-driven)
{_fmt_t2b(tipo2b)}

[T4] Hidden gems (1-5 studies, >=75% favorable, rarity-weighted)
{_fmt_t4(tipo4)}

[T6] Temporal anomalies (same intervention, very different rate pre/post 2021)
{_fmt_t6(tipo6)}

[T7] Contradictions (same intervention, both favorable and unfavorable studies)
{_fmt_t7(tipo7)}

[T8] KG 2-hop mechanistic hypotheses (both hops confirmed by >=2 papers each)
Note: KG covers ~32% of articles — these are preliminary paths, not proven mechanisms.
{_fmt_t8(tipo8)}

[T9] Pleiotropic signals (intervention improves secondary biomarkers in favorable studies)
{_fmt_t9(tipo9)}"""

    # PASO 1 — Gemma decide qué buscar en PubMed
    # Gemma entiende el contexto biológico completo de cada hipótesis.
    # Es mucho mejor que nosotros formulando queries porque:
    # - Conoce los términos MeSH y sinónimos usados en la literatura
    # - Puede identificar qué aspecto de la hipótesis es el más específico
    # - Sabe que "obesity SHBG PCOS" devuelve cosas distintas a "oxidative stress SHBG liver PCOS"
    # - Puede formular queries que testean la relación causal, no solo la co-ocurrencia
    prompt_paso1 = f"""Eres un investigador de PCOS con 15 años de experiencia.
Recibes los resultados de un scan de señales emergentes en 12.155 papers de PCOS.

CONTEXTO — LO QUE YA SE SABE (NO son señales nuevas):
- Primera línea: metformina, letrozol, clomifeno, espironolactona, ACOs
- Ya bien estudiados: inositol, berberina, curcumina, vitamina D, omega-3, probióticos
- Mecanismos conocidos: IR→andrógenos, LH alto→anovulación, gut→IR, obesidad→↓SHBG vía insulina
- GLP-1/liraglutide/semaglutide: ya mainstream en obesidad+PCOS

SEÑALES DEL SCAN (baseline favorable={baseline_rate:.0%}):
{signals_block}

TU TAREA:
Identifica las 4-6 hipótesis o señales que te parecen MÁS POTENCIALMENTE NUEVAS.
Para cada una, formula DOS tipos de query PubMed:

PROBLEMA CON QUERIES MUY ESPECÍFICAS: "SGLT2 inhibitors" AND "free androgen index"
AND "ovulation rate" AND "PCOS" puede devolver 0 resultados aunque el campo esté
activo — el AND de 4 frases exactas es demasiado estricto y pierde papers con
sinónimos (testosterone, FAI, menstrual cycle). Esto es un falso negativo peligroso.

SOLUCIÓN — usa SIEMPRE dos capas:

1. BROAD_QUERY: 2-3 términos clave, sin AND excesivos.
   Sirve para saber si el CAMPO existe (si >15 resultados → área activa).
   Ejemplo: "SGLT2 inhibitors" "polycystic ovary syndrome" androgens
   Ejemplo: cabergoline "polycystic ovary syndrome"

2. SPECIFIC_QUERY: 3-4 términos que capturen el ÁNGULO CONCRETO no estudiado.
   Incluye sinónimos entre paréntesis con OR cuando convenga.
   Ejemplo: "SGLT2" "PCOS" ("free androgen index" OR "testosterone") "ovulation"
   Ejemplo: cabergoline "GnRH pulse" OR "LH pulse" "polycystic"

Si BROAD da >15 pero SPECIFIC da 0-3 → hay campo pero el ángulo específico es nuevo.
Si BROAD da 0 → genuinamente nuevo.
Si ambos dan >15 → ya bien estudiado, baja prioridad.

FORMATO DE SALIDA — solo esto, nada más:

BLOQUE 1 — Las 4-6 hipótesis con mayor potencial de novedad (buscaremos en PubMed):
HIPOTESIS: <descripción en 1 frase de por qué te parece nova>
BROAD_QUERY: <2-3 términos, mide si el campo existe>
SPECIFIC_QUERY: <3-4 términos con OR donde haya sinónimos, mide si el gap específico existe>
---
HIPOTESIS: <siguiente>
BROAD_QUERY: <...>
SPECIFIC_QUERY: <...>
---
[máximo 6 hipótesis en este bloque]

BLOQUE 2 — Otras señales interesantes que no llegaron al top pero merecen seguimiento
(NO necesitan queries PubMed — solo una línea cada una):
OTRAS_SENALES:
- [entidad o patrón]: <1 frase explicando por qué es interesante y qué tipo de señal es (T1/T4/T7/T8/T9)>
- [entidad o patrón]: <1 frase>
[entre 4 y 8 entradas]
FIN"""

    fallback_text = (
        "_Síntesis automática (Ollama no disponible)_\n\n"
        f"Top señal T1: **{tipo1[0]['entity'] if tipo1 else 'N/A'}**. "
        f"Top modificador T2b: **{tipo2b[0]['modifier_value'] if tipo2b else 'N/A'}**. "
        "Ver tablas detalladas abajo.\n"
    )

    try:
        log.info("Síntesis Paso 1: Gemma analiza señales y formula queries de novedad...")
        paso1_text = _run_llm(prompt_paso1, num_predict=1000, temperature=0.25)

        # ---- Extraer queries y OTRAS_SENALES del output de Gemma (Paso 1) ----
        # Gemma produce dos tipos de queries: BROAD (campo general) y SPECIFIC (ángulo exacto).
        # También puede producir un bloque OTRAS_SENALES: con señales adicionales sin queries.
        # Las queries se ejecutan en PubMed; OTRAS_SENALES se pasan al Paso 2 como contexto.
        broad_queries: list[str] = []
        specific_queries: list[str] = []
        otras_senales_lines: list[str] = []
        in_otras_senales = False
        hypotheses_text = paso1_text  # texto completo para el reporte
        for line in paso1_text.splitlines():
            line_upper = line.strip().upper()
            q_raw = line.strip()
            # Detectar inicio del bloque OTRAS_SENALES
            if "OTRAS_SENALES" in line_upper or "OTRAS_SE" in line_upper:
                in_otras_senales = True
                continue
            # Detectar fin del bloque (FIN o nueva sección de queries)
            if in_otras_senales:
                if line_upper.startswith("FIN") or line_upper.startswith("HIPOTESIS"):
                    in_otras_senales = False
                elif q_raw.startswith("-") and len(q_raw) > 5:
                    otras_senales_lines.append(q_raw)
                continue
            if line_upper.startswith("BROAD_QUERY:"):
                q = q_raw[12:].strip().strip('"').strip("'")
                if q and len(q) > 5:
                    broad_queries.append(("BROAD", q))
            elif line_upper.startswith("SPECIFIC_QUERY:"):
                q = q_raw[15:].strip().strip('"').strip("'")
                if q and len(q) > 5:
                    specific_queries.append(("SPECIFIC", q))
            elif line_upper.startswith("QUERY:"):
                # Fallback: si Gemma no siguió el formato, tratar como specific
                q = q_raw[6:].strip().strip('"').strip("'")
                if q and len(q) > 5:
                    specific_queries.append(("SPECIFIC", q))

        queries = broad_queries + specific_queries  # broad primero
        otras_senales_block = (
            "\n".join(otras_senales_lines) if otras_senales_lines
            else "(Gemma no generó lista de otras señales)"
        )

        log.info("Paso 1 produjo %d queries PubMed. Ejecutando búsquedas...", len(queries))

        # ---- Paso 2a: Python ejecuta las queries en PubMed ----
        pubmed_results = _execute_llm_searches(queries)

        # PASO 2 — Gemma sintetiza con los resultados de búsqueda
        prompt_paso2 = f"""Eres un investigador de PCOS con 15 años de experiencia.
Acabas de analizar señales de un scan automático y formulaste queries para verificar
qué hipótesis ya han sido estudiadas directamente. Ahora tienes los resultados.

SEÑALES DEL SCAN (mismo contexto que antes):
{signals_block}

════════════════════════════════════════════════════════════════════
RESULTADOS DE TUS BÚSQUEDAS EN PUBMED
════════════════════════════════════════════════════════════════════
Interpretación:
  0 resultados → nadie estudió esto específicamente → hipótesis genuinamente nueva
  1-5 resultados → muy poco estudiado, revisar si son relevantes
  6-30 resultados → área activa pero posiblemente sin consenso
  >30 resultados → ya bien estudiado, baja prioridad como señal nueva
  [META-ANÁLISIS] en título → existe síntesis → señal establecida

{pubmed_results}

════════════════════════════════════════════════════════════════════
OTRAS SEÑALES IDENTIFICADAS EN PASO 1 (para incluir en la sección correspondiente)
════════════════════════════════════════════════════════════════════
{otras_senales_block}

════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE SÍNTESIS
════════════════════════════════════════════════════════════════════
Escribe en ESPAÑOL. Máximo 900 palabras. Sin tablas. 5 secciones exactas:

## Resumen ejecutivo
Patrón global del scan. Qué es ruido confirmado de consenso vs qué es genuinamente nuevo.
Sé específico — cita señales y números.

## Señales prioritarias para investigar (máximo 3)
Ordénadas por novedad REAL (combina señales del scan + resultados de PubMed).
Para cada una: (a) por qué es nueva según PubMed, (b) mecanismo biológico específico,
(c) en qué detectores aparece [T1/T4/T8/T9], (d) experimento que la confirmaría.
CALIDAD: evalúa cada salto de la hipótesis por separado — NO busques un paper que
confirme el path completo (eso refutaría la novedad, no la confirmaría).

## Hipótesis mecanísticas emergentes (2-3)
Hipótesis concretas que emergen de COMBINAR señales de distintos detectores.
"Si [A], entonces [predicción específica], testable mediante [experimento].
Combina [T?] con [T?]."
Solo hipótesis que NO existen ya en la literatura según los resultados de PubMed.

## Otras señales que merecen seguimiento
Lista de señales que quedaron fuera del top pero son interesantes.
Incluye las que Gemma listó en OTRAS_SENALES (Paso 1) + cualquier otra del scan que veas relevante.
Para cada una: **[entidad/patrón]** (tipo T?) — 2-3 frases: qué es interesante, qué falta estudiar.
Mínimo 4 entradas, máximo 8.

## Señales que son probablemente ruido
Brutalmente honesto. ¿Cuáles son: (a) ya consenso según PubMed, (b) sesgo regional,
(c) un solo paper sin mecanismo, (d) alucinación del KG sparse?"""

        log.info("Síntesis Paso 2: Gemma sintetiza con resultados de PubMed...")
        synthesis_text = _run_llm(prompt_paso2, num_predict=1600, temperature=0.20)

        if not synthesis_text:
            return fallback_text, pubmed_results

        # Construir el bloque de auditoría completo para el reporte
        audit_block = (
            "### Hipótesis que Gemma identificó como candidatas (Paso 1)\n\n"
            f"```\n{hypotheses_text}\n```\n\n"
            "### Resultados de búsqueda en PubMed (Paso 2)\n\n"
            f"```\n{pubmed_results}\n```"
        )

        return synthesis_text + "\n", audit_block

    except Exception as exc:
        log.warning("LLM synthesis failed (non-critical): %s", exc)
        return fallback_text, ""


# REPORT WRITER

def _write_report(
    tipo1: list[dict],
    tipo2: list[dict],
    tipo2b: list[dict],
    tipo3: list[dict],
    tipo4: list[dict],
    tipo6: list[dict],
    tipo7: list[dict],
    tipo8: list[dict],
    tipo9: list[dict],
    top_n: int,
    conn: sqlite3.Connection | None = None,   # para búsqueda de evidencia directa
    max_year: int | None = None,              # temporal holdout cutoff
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    year_suffix = f"_holdout{max_year}" if max_year is not None else ""
    path = REPORTS_DIR / f"anomaly_scan_v2_report_{timestamp}{year_suffix}.md"

    cutoff_note = (
        f"> **Temporal holdout mode**: solo articulos publicados en o antes de {max_year}.\n"
        "> Los resultados se usan para evaluacion retrospectiva — no sobreescribe el scan completo.\n"
    ) if max_year is not None else ""

    lines = [
        "# Anomaly Scan v2 — PCOS Senales Emergentes",
        "",
        "> Filosofia: buscamos anomalias, no rankings de medicamentos conocidos.",
        "> El score favorece rareza + consistencia. Metformin no aparecera aqui.",
        "",
        cutoff_note,
        f"_Senales encontradas: T1(cross-indication)={len(tipo1)} | "
        f"T2(subpoblacion)={len(tipo2)} | T3(outcome inesperado)={len(tipo3)} | "
        f"T4(hidden gems)={len(tipo4)} | T6(temporal)={len(tipo6)} | "
        f"T7(contradicciones)={len(tipo7)} | T8(kg-convergence)={len(tipo8)} | "
        f"T9(pleiotropia)={len(tipo9)}_",
        "",
        "---",
        "",
        "## 🔬 Síntesis del investigador (LLM)",
        "",
        "> Esta sección es generada por Gemma después de leer todas las señales.",
        "> Conecta patrones transversales, propone hipótesis mecanísticas y",
        "> distingue señales reales de ruido. Las tablas detalladas siguen abajo.",
        "",
    ]

    # Compute baseline favorable rate for the synthesis prompt
    _baseline = 0.38  # default
    try:
        import sqlite3 as _sq
        _conn = _sq.connect(str(PROCESSED_DIR / "pcos_research.db"), timeout=5)
        _row = _conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN effect_direction='favorable' THEN 1 ELSE 0 END) "
            "FROM article_extractions WHERE effect_direction IS NOT NULL"
        ).fetchone()
        _conn.close()
        if _row and _row[0]:
            _baseline = round(_row[1] / _row[0], 3)
    except Exception:
        pass

    direct_evidence_str = ""  # legacy, no longer used — Gemma now directs PubMed searches

    log.info("Generating LLM synthesis — 2-pass loop with Gemma-directed PubMed search...")
    synthesis_text, pubmed_audit = _generate_synthesis(
        tipo1, tipo2b, tipo4, tipo6, tipo7, tipo8, tipo9, _baseline,
    )
    lines.append(synthesis_text)
    lines += ["---", ""]

    # ---- Bloque de auditoría PubMed (lo que Gemma buscó y qué encontró) ----
    if pubmed_audit:
        lines += [
            "## 🔍 Auditoría de Novedad — Búsqueda PubMed dirigida por Gemma",
            "",
            "> Gemma identificó qué hipótesis buscar (Paso 1) y recibió los",
            "> resultados antes de escribir la síntesis (Paso 2).",
            "> 0 resultados = hipótesis genuinamente nueva; >30 = ya estudiada.",
            "",
            pubmed_audit,
            "",
            "---",
            "",
        ]

    # ---- TIPO 4 first — hidden gems are the most valuable ----
    lines += [
        "## Tipo 4 — Hidden Gems (raros pero consistentes)",
        "",
        "> Intervenciones en muy pocos estudios (1-5) con alta consistencia favorable.",
        "> Estos son los casos que nadie ha leido y cruzado entre si.",
        "> Alta prioridad para investigacion futura.",
        "",
    ]
    if not tipo4:
        lines.append(
            "_No se detectaron hidden gems. Posiblemente pocos estudios tienen "
            "effect_direction bien extraido. Correr mas extracciones v1.1._"
        )
    else:
        for sig in tipo4[:top_n]:
            mixed_str = f" | Mixed: {sig['n_mixed']}" if sig["n_mixed"] > 0 else ""
            lines += [
                f"### [T4] {sig['entity']}",
                f"- Estudios: {sig['n_studies']} | Favorables: {sig['n_favorable']}{mixed_str}"
                f" | Tasa favorable: {sig['favorable_rate']:.0%}"
                f" | N medio: {sig['mean_sample_size']:.0f}"
                f" | Rareza: {sig['rarity_factor']:.2f}"
                f" | **Score: {sig['curiosity_score']}**",
                "",
                "| Año | ID | Tipo estudio | Efecto | N | Outcomes |",
                "|---|---|---|---|---|---|",
            ]
            for art in sig["articles"]:
                outs = _parse_outcomes(art.get("main_outcomes", []))
                lines.append(
                    f"| {art.get('year', '?')} "
                    f"| {art.get('canonical_id', '?')[:40]} "
                    f"| {art.get('study_type', '?')} "
                    f"| {art.get('effect_direction', '?')} "
                    f"| {art.get('n_total', '?')} "
                    f"| {', '.join(outs[:3]) or 'n/a'} |"
                )
            lines.append("")

    lines += ["---", ""]

    # ---- TIPO 1 ----
    lines += [
        "## Tipo 1 — Cross-Indication Signals (Drug Repurposing)",
        "",
        "> Farmacos NO disenados para PCOS que aparecen con efecto favorable.",
        "> Score ajustado por rareza: 2/3 estudios favorables > 5/200.",
        "",
    ]
    if not tipo1:
        lines.append("_No se detectaron senales tipo 1 con los umbrales actuales._")
    else:
        for sig in tipo1[:top_n]:
            mixed_str = f" | Mixed: {sig['n_mixed']}" if sig["n_mixed"] > 0 else ""
            lines += [
                f"### [T1] {sig['entity']}",
                f"- Estudios: {sig['n_studies']} | Favorables: {sig['n_favorable']}{mixed_str}"
                f" | Consistencia: {sig['consistency']:.0%}"
                f" | Rareza: {sig['rarity_factor']:.2f}"
                f" | **Score: {sig['curiosity_score']}**",
                "",
                "| Ano | ID | Tipo | Efecto | Outcomes |",
                "|---|---|---|---|---|",
            ]
            for art in sig["articles"]:
                outs = _parse_outcomes(art.get("main_outcomes", []))
                lines.append(
                    f"| {art.get('year', '?')} "
                    f"| {art.get('canonical_id', '?')[:40]} "
                    f"| {art.get('study_type', '?')} "
                    f"| {art.get('effect_direction', '?')} "
                    f"| {', '.join(outs[:3]) or 'n/a'} |"
                )
            lines.append("")

    lines += ["---", ""]

    # ---- TIPO 2 ----
    lines += [
        "## Tipo 2 — Subpopulation Variance",
        "",
        "> Misma intervencion, tasa de exito muy diferente segun subgrupo.",
        "> Dimension: dieta, IMC, etnia, comorbilidades.",
        "> Umbral: diferencia >= 30pp entre mejor y peor subgrupo.",
        "",
    ]
    if not tipo2:
        lines.append(
            "_No se detectaron senales tipo 2. Cobertura de campos population_*"
            " aun baja — aumentar con mas extracciones v1.1._"
        )
    else:
        for sig in tipo2[:top_n]:
            lines += [
                f"### [T2] {sig['entity']} — dimension: {sig['dimension']}",
                f"- Rango: {sig['rate_range']:.0%} | **Score: {sig['curiosity_score']}**",
                f"- Mejor: **{sig['best_subgroup']['subpop']}** "
                f"({sig['best_subgroup']['n_favorable']}/{sig['best_subgroup']['n']} "
                f"= {sig['best_subgroup']['fav_rate']:.0%})",
                f"- Peor:  **{sig['worst_subgroup']['subpop']}** "
                f"({sig['worst_subgroup']['n_favorable']}/{sig['worst_subgroup']['n']} "
                f"= {sig['worst_subgroup']['fav_rate']:.0%})",
                "",
                "| Subgrupo | N | N fav | Tasa |",
                "|---|---|---|---|",
            ]
            for sub in sig["all_subgroups"]:
                lines.append(
                    f"| {sub['subpop']} | {sub['n']} | "
                    f"{sub['n_favorable']} | {sub['fav_rate']:.0%} |"
                )
            lines.append("")

    lines += ["---", ""]

    # ---- TIPO 2b ----
    lines += [
        "## Tipo 2b — Cross-Intervention Hidden Modifiers",
        "",
        "> EL DETECTOR DE VARIABLES OCULTAS.",
        "> Caracteristica de subpoblacion que predice mejores resultados",
        "> INDEPENDIENTEMENTE de cual sea la intervencion.",
        "> Si 'vegan' tiene 80% favorable en berberina, inositol Y omega-3,",
        "> la dieta (no el farmaco) puede ser el driver real.",
        "> Umbral: delta >= 12pp sobre baseline, en >= 2 intervenciones distintas.",
        "",
    ]
    if not tipo2b:
        lines.append(
            "_No se detectaron modificadores transversales. "
            "Se necesitan mas extracciones con campos population_diet/bmi/ethnicity rellenos._"
        )
    else:
        for sig in tipo2b[:top_n]:
            interventions_str = ", ".join(sig["sample_interventions"][:4])
            lines += [
                f"### [T2b] {sig['modifier_value']} (dimension: {sig['dimension']})",
                f"- **Tasa favorable: {sig['favorable_rate']:.0%}** "
                f"(baseline: {sig['baseline_rate']:.0%}, delta: +{sig['delta_vs_baseline']:.0%})",
                f"- n_estudios: {sig['n_studies']} | n_favorable: {sig['n_favorable']}",
                f"- Intervenciones DISTINTAS cubriendo este subgrupo: {sig['n_distinct_interventions']}",
                f"- Intervenciones: {interventions_str}",
                f"- Periodo: {sig.get('year_range', 'n/a')}",
                f"- **Score: {sig['curiosity_score']}**",
                f"- Interpretacion: {sig['anomaly_reason']}",
                "",
            ]

    lines += ["---", ""]

    # ---- TIPO 3 ----
    lines += [
        "## Tipo 3 — Unexpected Outcome Co-occurrence",
        "",
        "> Outcomes que aparecen repetidamente en estudios de una intervencion",
        "> pero NO son outcomes esperados en PCOS.",
        "> Pueden indicar mecanismos pleiotropicos no estudiados.",
        "",
    ]
    if not tipo3:
        lines.append("_No se detectaron senales tipo 3 con los umbrales actuales._")
    else:
        for sig in tipo3[:top_n]:
            lines += [
                f"### [T3] {sig['entity']} ({sig['n_studies_total']} estudios)",
                "",
                "| Outcome inesperado | N estudios donde aparece |",
                "|---|---|",
            ]
            for uo in sig["unexpected_outcomes"]:
                lines.append(f"| {uo['outcome']} | {uo['n_studies']} |")
            lines.append("")

    # ---- TIPO 6 ----
    lines += [
        "## Tipo 6 — Temporal Anomaly (evidencia creciente o no-replicacion)",
        "",
        "> Misma intervencion, tasa favorable muy diferente en estudios antiguos vs recientes.",
        "> 'rising': evidencia convergente — cada vez mas estudios lo confirman.",
        "> 'falling': no-replicacion — exito inicial no se sostiene en trials mas grandes/nuevos.",
        "> Umbral: diferencia >= 25pp entre eras, >= 2 estudios en cada era.",
        "",
    ]
    if not tipo6:
        lines.append(
            "_No se detectaron anomalias temporales. "
            "Puede indicar pocos estudios por intervencion o distribucion uniforme en el tiempo._"
        )
    else:
        for sig in tipo6[:top_n]:
            trend_label = "📈 RISING (evidencia convergente)" if sig["trend"] == "rising" else "📉 FALLING (no-replicacion)"
            lines += [
                f"### [T6] {sig['entity']} — {trend_label}",
                f"- Pre-{sig['year_cutoff'] + 1}: **{sig['fav_rate_old']:.0%}** favorable (n={sig['n_old']})",
                f"- Post-{sig['year_cutoff']}: **{sig['fav_rate_recent']:.0%}** favorable (n={sig['n_recent']})",
                f"- Delta: {sig['delta']:+.0%} | **Score: {sig['curiosity_score']}**",
                f"- {sig['anomaly_reason']}",
                "",
            ]

    lines += ["---", ""]

    # ---- TIPO 7 ----
    lines += [
        "## Tipo 7 — Contradiction Analysis (misma intervencion, efectos opuestos)",
        "",
        "> Intervenciones con estudios TANTO favorables COMO desfavorables.",
        "> El detector busca el diferenciador estructural: BMI, etnia, tipo de estudio, año.",
        "> Un diferenciador fuerte = hipotesis mecanistica sobre en quien funciona.",
        "",
    ]
    if not tipo7:
        lines.append("_No se detectaron contradicciones con los umbrales actuales._")
    else:
        for sig in tipo7[:top_n]:
            diff = sig.get("top_differentiator")
            lines += [
                f"### [T7] {sig['entity']}",
                f"- Favorables: {sig['n_favorable']} | Desfavorables: {sig['n_unfavorable']}"
                f" | Total: {sig['n_total']} | **Score: {sig['curiosity_score']}**",
            ]
            if diff:
                lines += [
                    f"- **Diferenciador top: `{diff['field']}`** ({diff['strength']})",
                    f"  - En estudios favorables:    {diff['in_favorable']}",
                    f"  - En estudios desfavorables: {diff['in_unfavorable']}",
                ]
            if len(sig["all_differentiators"]) > 1:
                others = [d["field"] for d in sig["all_differentiators"][1:]]
                lines.append(f"- Otros diferenciadores: {', '.join(others)}")
            lines += [f"- {sig['anomaly_reason']}", ""]

    lines += ["---", ""]

    # ---- TIPO 8 — KG Convergence ----
    lines += [
        "## Tipo 8 — KG Convergence (hipótesis mecanísticas emergentes)",
        "",
        "> Caminos de DOS SALTOS en el grafo de mecanismos donde AMBOS saltos",
        "> están confirmados por >= 2 papers independientes.",
        "> A --[r1]--> B --[r2]--> C  donde A=intervención, B=mecanismo, C=endpoint PCOS.",
        "> Ningún paper dice 'A afecta C vía B' — es una hipótesis emergente del grafo.",
        "",
    ]
    if not tipo8:
        lines.append(
            "_No se detectaron hipótesis convergentes. KG aún poco poblado "
            "(solo 32% de artículos tienen triples). Mejorar cobertura de mechanism_links._"
        )
        lines.append("")
    else:
        for sig in tipo8[:top_n]:
            lines += [
                f"### [T8] {sig['drug']} → {sig['mechanism']} → {sig['endpoint']}",
                f"- **Hop 1:** `{sig['drug']}` --[{sig['relation_hop1']}]--> `{sig['mechanism']}` "
                f"| {sig['n_papers_hop1']} papers | conf avg={sig['avg_conf_hop1']}",
                f"- **Hop 2:** `{sig['mechanism']}` --[{sig['relation_hop2']}]--> `{sig['endpoint']}` "
                f"| {sig['n_papers_hop2']} papers | conf avg={sig['avg_conf_hop2']}",
                f"- **Score de convergencia:** {sig['convergence_score']}  "
                f"_(= {sig['n_papers_hop1']} × {sig['n_papers_hop2']} × avg_conf)_",
                f"- **Hipótesis emergente:** _{sig['hypothesis']}_",
                "",
                f"  Papers hop 1: {', '.join(sig['papers_hop1'])}",
                f"  Papers hop 2: {', '.join(sig['papers_hop2'])}",
                "",
            ]

    lines += ["---", ""]

    # ---- TIPO 9 ----
    lines += [
        "## Tipo 9 — Secondary Biomarker Movement (señales pleiotropicas)",
        "",
        "> En estudios FAVORABLES, esta intervencion mejora marcadores fuera de PCOS.",
        "> Diferencia de Tipo 3: solo cuenta estudios favorables y agrupa por categoria clinica.",
        "> Señala beneficios pleiotropicos: cardiovascular, inflamacion, microbioma, etc.",
        "",
    ]
    if not tipo9:
        lines.append(
            "_No se detectaron señales pleiotropicas. "
            "Puede indicar pocos estudios favorables con outcomes detallados._"
        )
    else:
        for sig in tipo9[:top_n]:
            lines += [
                f"### [T9] {sig['entity']} — top: {sig['top_category']}",
                f"- Estudios favorables: {sig['n_favorable_studies']} | **Score: {sig['curiosity_score']}**",
                f"- {sig['anomaly_reason']}",
                "",
                "| Categoria | N hits | Outcomes ejemplo |",
                "|---|---|---|",
            ]
            for s in sig["secondary_signals"]:
                lines.append(
                    f"| {s['category']} | {s['n_hits']} "
                    f"| {', '.join(s['example_outcomes'][:2])} |"
                )
            lines.append("")

    lines += ["---", ""]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Report written to %s", path)

    # Keep a "latest" copy for quick access — skip in holdout mode to avoid overwriting full scan
    if max_year is None:
        latest = REPORTS_DIR / "anomaly_scan_v2_report_latest.md"
        shutil.copy2(path, latest)
        log.info("Latest copy: %s", latest)

    return path


# MAIN

def anomaly_scan_v2(min_studies: int = 2, top_n: int = 25, max_year: int | None = None) -> Path:
    db_path = PROCESSED_DIR / "pcos_research.db"
    if not db_path.exists():
        log.error("DB not found: %s", db_path)
        raise FileNotFoundError(db_path)

    if max_year is not None:
        log.info("Temporal holdout mode: restricting to papers published <= %d", max_year)

    with sqlite3.connect(db_path, timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")

        # Check if entity tables exist
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        if "entity" not in tables or "article_entity_links" not in tables:
            log.error(
                "Entity tables not found. Run entity_normalizer.py first.\n"
                "Tables present: %s", tables
            )
            raise RuntimeError("entity_normalizer must run before anomaly_scan_v2")

        log.info("Loading data...")
        entity_signals = _load_entity_signals(conn)
        links_df = _load_entity_links(conn, max_year=max_year)

        log.info(
            "Data loaded: %d entity signals | %d entity-article links",
            len(entity_signals), len(links_df),
        )

        # Load raw extractions for cross-intervention analysis (Tipo 2b)
        extractions_df = _load_extractions(conn, max_year=max_year)
        log.info("  Extractions loaded: %d rows", len(extractions_df))
        n_all = len(extractions_df)
        n_fav_all = int((extractions_df["effect_direction"] == "favorable").sum()) if n_all > 0 else 0
        baseline_fav = n_fav_all / n_all if n_all > 0 else 0.5
        log.info("  Baseline favorable rate: %.1f%% (%d/%d)", baseline_fav * 100, n_fav_all, n_all)

        # ---- Run detectors ----
        log.info("Detecting Tipo 4 (hidden gems: rare but consistent)...")
        tipo4 = detect_tipo4_hidden_gems(links_df, max_studies=5, min_favorable_rate=0.75)
        log.info("  Found %d Tipo 4 hidden gems", len(tipo4))

        log.info("Detecting Tipo 1 (cross-indication, rarity-adjusted)...")
        tipo1 = detect_tipo1(links_df, min_favorable=min_studies)
        log.info("  Found %d Tipo 1 signals", len(tipo1))

        log.info("Detecting Tipo 2 (subpopulation variance within intervention)...")
        tipo2 = detect_tipo2(links_df, min_per_group=min_studies)
        log.info("  Found %d Tipo 2 signals", len(tipo2))

        log.info("Detecting Tipo 2b (cross-intervention hidden modifiers)...")
        tipo2b = detect_tipo2b_cross_intervention(
            extractions_df, baseline_fav, min_studies=max(min_studies, 3), min_delta=0.12,
        )
        log.info("  Found %d Tipo 2b cross-intervention modifiers", len(tipo2b))

        log.info("Detecting Tipo 3 (unexpected outcome co-occurrence)...")
        tipo3 = detect_tipo3(links_df, min_co_occurrence=min_studies)
        log.info("  Found %d Tipo 3 signals", len(tipo3))

        log.info("Detecting Tipo 6 (temporal anomaly: rising vs falling evidence)...")
        tipo6 = detect_tipo6_temporal(links_df)
        log.info("  Found %d Tipo 6 temporal signals", len(tipo6))

        log.info("Detecting Tipo 7 (contradiction analysis: same drug, opposite outcomes)...")
        tipo7 = detect_tipo7_contradictions(links_df)
        log.info("  Found %d Tipo 7 contradictions", len(tipo7))

        log.info("Detecting Tipo 9 (secondary biomarker movement: pleiotropic signals)...")
        tipo9 = detect_tipo9_secondary_biomarkers(links_df)
        log.info("  Found %d Tipo 9 pleiotropic signals", len(tipo9))

        log.info("Detecting Tipo 8 (KG convergence: emergent 2-hop mechanistic hypotheses)...")
        tipo8 = detect_tipo8_kg_convergence(conn, min_papers_per_edge=2, min_score=1.5)
        log.info("  Found %d Tipo 8 emergent hypotheses", len(tipo8))

        report_path = _write_report(
            tipo1, tipo2, tipo2b, tipo3, tipo4, tipo6, tipo7, tipo8, tipo9,
            top_n, conn=conn, max_year=max_year,
        )

    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PCOS Anomaly Scan v2 — emergent signal detection"
    )
    parser.add_argument(
        "--min-studies", type=int, default=2,
        help="Minimum number of studies to consider a signal (default: 2)"
    )
    parser.add_argument(
        "--top-n", type=int, default=25,
        help="Max signals to show per type in report (default: 25)"
    )
    parser.add_argument(
        "--max-year", type=int, default=None,
        help="Temporal holdout cutoff: only use papers published <= this year. "
             "Report saved separately, does NOT overwrite latest. Example: --max-year 2020"
    )
    args = parser.parse_args()

    report = anomaly_scan_v2(min_studies=args.min_studies, top_n=args.top_n, max_year=args.max_year)
    print(f"Anomaly scan v2 report: {report}")
