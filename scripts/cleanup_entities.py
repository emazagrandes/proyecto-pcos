"""
Entity Cleanup Script v2
========================
Cleans garbage from the `entity` table and reclassifies entities with wrong entity_type.

Actions:
  1. DELETE  — pure garbage with no analytical value
  2. RECLASSIFY — entities with value but wrong entity_type

Run:
    python scripts/cleanup_entities.py --preview      # show what will change, no writes
    python scripts/cleanup_entities.py --execute      # apply changes
"""

import sqlite3
import sys
import argparse
from pathlib import Path

# Fix Windows cp1252 console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path("data/processed/pcos_research.db")

# ─────────────────────────────────────────────────
# 1. ENTITIES TO DELETE COMPLETELY
# ─────────────────────────────────────────────────

DELETE_EXACT = {
    # Generic/placeholder
    "null", "study", "drug", "evaluation", "measurement", "energy", "function",
    "general health", "medical treatment", "standard care program", "standard intervention",
    "usual care", "conventional intervention", "combination of treatments",
    "no intervention provided", "no intervention study", "no intervention (observational study)",
    "untreated control", "active comparator", "placebo group", "placebos", "plasebo",
    "placebo administration", "placebo alone", "placebo pills", "placebo tablets",
    "placebo supplement", "placebo oral tablet", "sugar pill",

    # Control groups — not interventions
    "control group", "control women", "healthy controls", "matched controls",
    "non-pcos controls", "control group without pcos", "controls",
    "women without any pcos features", "women without pcos",
    "control participants without pcos",

    # The condition itself
    "polycystic ovary syndrome", "polycystic ovary syndrome (pcos)", "pcos",
    "pcos (ovulatory status)", "different pcos",

    # Data collection procedures (no therapeutic/diagnostic value)
    "blood sampling", "blood collection", "blood samples", "blood test", "blood work",
    "serum", "urine collection", "stool collection", "saliva samples",
    "questionnaire administration", "data collection",
    "collect body fluids/tissues & med history", "frequent baseline blood sampling",
    "venous puncture", "peripheral phlebotomy", "phlebotomy",
    "blood samples, transvaginal ultrasound",
    "blood test, ultrasound", "clinical, biophysical", "clinical data collection",
    "biochemical blood tests", "biochemical, hormonal", "hormonal parameters",
    "hormonal levels", "hormonal", "hormonal contraception",
    "genetic analysis", "qrtpcr (mrna level).",

    # Pure measurement labels (not interventions)
    "serum creatinine", "serum creatinine every month", "waist circumference (cm)",
    "serum marker levels", "measurments", "hormonal", "measurements",
    "body composition", "visceral fat thickness", "cardiac risk ratio (crr)",
    "all the indicators", "blood sugar", "glucose", "water", "fat",

    # Biomarker/lab test collections that aren't real entities
    "serum levels of lh, fsh, testosterone, prolactin,",
    "day 3: follicle stimulating hormone (fsh), luteinizing hormone (lh), thyroid stimulating hormone (tsh), total testosterone",
    "serum total testosterone, serum androsterone, serum androstenedione",
    "serum estradiol (e2) on day 12", "serum progesterone on day 21",
    "serum dehydroepiandrosterone sulfate", "serum uc-oc",
    "dha levels of blood", "amylin level", "leptin concentration in blood serum",
    "omentin-1 concentration in blood serum", "resistin concentration in blood serum",
    "hepassocin", "clusterin level", "preptin",
    "measurement of bisphenol in urine",
    "measurement of fasting tumor necrosis factor α (tnf-α) concentration",
    "measurement of fetuin-a level in serum", "measurement of ghrelin concentration",
    "measurement of interleukin-18 (il-18) concentration",
    "measurement of interleukin-4 (il-4) concentration",
    "measurement of interleukin-6 (il-6) concentration in blood serum",
    "measurement of kisspeptin concentration", "measurement of zonulin concentration",
    "measurement of oxidative stress levels (malondialdehide, glutathione disulphate, total antioxidant capacity, superoxide dismutase",
    "measurement of bisphenol in urine",
    "frequency of chronic vascular complications [n (%)]",
    "time in hyperglycemia (hours)", "time in target range (hours)",
    "high-density lipoprotein (hdl) (mg/dl)", "low-density lipoprotein (ldl) (mg/dl)",
    "total cholesterol", "triglycerides (mg/dl)", "mean glucose (mg/dl)",
    "waist-to-hip ratio", "insulin sensitivity", "insulin dose (ui/kg)",
    "body mass index (bmi) calculation",

    # ML methods used for data analysis (not interventions)
    "machine learning models (lr, rf, dt, nb, svm, knn, xgboost, adaboost)",
    "smote-enn", "bioinformatics analysis",
    "optimized feature selection, bayesian optimization,",
    "chromatography", "raman spectrum", "fourier transform ion cyclotron resonance mass spectrometry",
    "differential ultracentrifugation", "optiprep™ density gradient ultracentrifugation",
    "size-exclusion chromatography", "metabolomics", "metabolomics analysis",
    "metabolic phenotyping", "differential ultracentrifugation",

    # Genetic polymorphisms (not clinical interventions)
    "gclc c-129 t", "gclm c-588 t polymorphisms", "mpo g-463a",
    "cyba c242t genetic polymorphisms",

    # Garbled / truncated names
    "assessment of the impact of imbalance between anti-",
    "ultraviolet radiatio",
    "3 mg drsp/20 μg ee",
    "subjects in the intervention group will receive one capsule containing 10 mg astaper day made by the \"zyest technology tarawat zendig\" institute in iran. the dosage of asx is determined based on the s",
    "effects of aidiet intervention to improve diet quality, immuno-metabolic health in normal",
    "patients (women of reproductive age suffering from non-alcoholic fatty liver",
    "environmental exposure to pfas (including legacy, branched-chain isomers,",
    "survey on patient's perspectives on the development of an structured education programme for pcos",
    "pcos (newly diagnosed) of adolescent age group will be assessed",
    "pcos (newly diagnosed) of adult age group will be assessed",
    "polycystic ovary syndrome) receiving 500 mg curcumin capsules (prepared from the extraction of turmeric in the laborat",
    "assessment of the severity of endogenetic alopecia using the visual ludwig scale",
    "assessment of the severity of hirsutism using the visual modified ferriman-gallwey scale",

    # Population descriptors labeled as interventions
    "female patients", "overweight pcos girls",
    "normal body mass index (bmi)", "high body mass index (bmi)",
    "normal ad libitum diet", "control diet", "standard diet", "standart diet therapy",

    # Study protocol / administrative
    "long-term follow-up", "longitudinal follow up", "screening evaluation",
    "cross-sectional community based study", "piloting the structured education programme for pcos",
    "investigating clinically normal patients", "no hormone",
    "biochemical assessment of young females",
    "cardiovascular autonomic function studies",
    "cardiovascular autonomic reflex tests (carts)",
    "endocrine assessment", "metabolic work-up", "cardiac work-up",

    # "Placebo" variants of specific drugs — keep placebo itself, delete redundant variants
    "placebo (folic acid )", "placebo (olive oil) supplement", "placebo (psyllium)",
    "placebo (wheat flour)", "placebo dlbs3233", "placebo laser acupoint stimulation",
    "placebo letrozole", "placebo levocarnitine", "placebo liraglutide pen injector",
    "placebo metformin", "placebo auricular acupressure", "placebo caplet of metformin xr",
    "placebo capsule of dlbs3233", "placebo to match azd4901",
    "placebo ultrasound at acupuncture points", "sham auricular acupoints acupressure",
    "sham-acupuncture group", "cc placebo", "bushen culuan decoction placebo",
    "clomiphene citrate tablets placebo", "myo-inositol placebo",
    "tanshinone placebo", "placebo levocarnitine", "placebo supplement",
    "active comparator: lifestyle counseling arm 1",
    "placebo comparator: lifestyle counseling dinner diet arm 2",

    # Random objects / reagents / animal model doses
    "cdcl2 (100 ppm in drinking water for 30 days)",
    "co-exposure to 5α-dihydrotestosterone (dht)",
    "excess testosterone (t) or dehydroepiandrosterone (dhea)",
    "insulin from gestational day 7.5 to 13.5",
    "vehicle (positive control), metformin (300mg/kg orally), or combination of metformin",
    "glyceryl tridecanoate", "maltodextrin", "soybean oil", "crispbread",
    "aventis pharma s.ae, global napi pharmaceuticals, cairo, egypt",

    # Generic aggregates (too vague to be an entity)
    "its generics", "supplements", "pelvis", "endocrine",
    "fertility treatment", "ovulatory agent", "allopathic medicine",
    "any drug not known as a major teratogen or major fetotoxicant",
    "pharmacotherapeutic", "non-pharmacotherapeutic interventions (metformin, oral contraceptives, antiandrogens, inositols, glp-1 agonists, dpp-4 inhibitors, sglt2 inhibitors, vitamin d, statins, letrozole, electrolysis, laser, eflornithine, acupuncture, herbal medicine)",
    "multiple (metformin, thiazolidinediones, statins, incretins, vitamin d, acarbose, myoinositol, clomiphene citrate, aromatase inhibitors)",
    "surgical treatments (lifestyle modifications, clomiphene citrate, metformin, myoinositol, ovarian drilling, ivf)",
    "lifestyle modifications, diet patterns, nutrients, pharmacological",
    "repurposed medications (hmg-coa reductase inhibitors, thiazolidinediones, sglt-2 inhibitors, dpp-4 inhibitors, glp-1 receptor agonists, mucolytic agents,",
    "combination of a plant extract (bsl_ep044)",
    "dietary interventions (including mediterranean diet, ketogenic diet, dash diet)",
    "exercise interventions (vigorous aerobic exercise, resistance/strength training, yoga)",
    "nutritional strategies/dietary patterns",
    "probiotics, prebiotics, fecal microbiota transplant (fmt), mirna therapy",
    "metformin (met), glucagon-like peptide-1 receptor agonists (glp-1 ras), thiazolidinediones (tzds), compound oral contraceptives (cocs), inositol (mi), vitamin d,",
    "herbal remedies (including glycyrrhiza glabra l., aloe vera, silybum marianum, serenoa repens, actaea racemosa l.,",
    "concentrations of c-reactive protein (crp), interleukin-1 (il-1), il-6, il-10, tumor necrosis factor (tnf-alpha) in pcos phenotypes a, b, c",
    "concentrations of crp, procalcitonin, fibrinogen, ferritin, il-1, il-6, il-10, tnf-alpha in both study arms",
    "evaluation of the correlation of serum concentrations of selected inflammatory markers (leucocytosis, crp, il-1, il-6, il-10, tnf-alpha)",
    "comparison of leucocytosis",
    "comparison of laboratory test results in women in the 4 study arms",
    "evaluation of the impact of subclinical hypothyroidism,",
    "metabolic response to protein source",
    "pro-inflammatory factors in women",
    "pro-inflammatory factors in women in both study arms",
    "hpod phenotypes on ovarian reserve indices",
    "detect the immune function of peripheral blood samples",
    "determination of concentrations of androgens",
    "diagnostic laboratory biomarker analysis",
    "clinical hyperandrogenism assessment",
    "clinical hyperandrogenism",
    "take the patient's subcutaneous fat tissue to detect the expression of lnk",
    "salivary samples will be collected. asprosin levels will be determined by biochemical analysis",
    "serum samples will be collected. asprosin levels will be determined by biochemical analysis",
    "experimental evaluation of ogn",
    "breast ultrasonography findings",
    "anogenital distance measurement",
    "scube-3 measurement",
    "amh level difference between patient",
    "anti-müllerian hormone (amh) as a diagnostic marker",
    "basal antral follicle count",
    "follicular growth",
    "vitamin d level assessment", "vitamin d levels measurement using chemiluminescent assay",
    "insulin sensitivity",

    # HOMA-IR duplicates (already a biomarker)
    "homa-ir，eshre/asrm",

    # Redundant dose-specific variants where canonical exists
    "500 mg/day curcumin", "astaxanthin 8 mg", "cabergoline 0.5 mg",
    "melatonin 3mg", "magnesium 500 mg", "l-carnitine 1000 mg",
    "levocarnitine 1000 mg", "folic a.",
    "20 mcg ethinylestradiol /3 mg drospirenone",
    "metformin (1000 mg daily), pioglitazone (30 mg daily), acetyl-l-carnitine (3 gm daily)",
    "metformin (500 mg twice a day), pioglitazone (15 mg twice a day)",
    "metformin 1500 mg", "metformin 1500 mg daily", "metformin 2250 mg daily",
    "metformin 500 mg oral tablet",
    "bicalutamide 50 mg",
    "letrozole 2.5mg", "letrozole 2.5mg-7.5mg", "letrozole oral tablet",
    "linagliptin 10 mg", "sitagliptin 100mg", "dexcom continuous glucose monitor (cgm)",
    "vildagliptin 50 mg", "raloxifene",
    "dydrogesterone (duphaston, abbott)", "dydrogesterone 10 mg oral tablet",
    "escitalopram 20 mg", "olive oil 5ml/5mg (bd) nutritional sachet 2100mg (bd)",
    "acarbose 100 mg", "subcutaneous semaglutide 1.0 mg once weekly",
    "letrozole-metformin", "letrozole-metformin-pioglitazone",
    "metformin-glp-1 receptor agonist", "metformin-oral contraceptive(oc)",
    "metformin, pioglitazone",
    "metformin, ethinylestradiol 30µg-drospirenone",
    "induction of ovulation using clomiphene citrate-pioglitazone-metformin",
    "induction of ovulation using letrozole-pioglitazone-metformin",
    "pioglitazone hydrochloride",
    "oral isotretinoin",
    "progesterone 400 mg vaginal suppository on pcos",
    "dydrogesterone tablets, norethisterone acetate, ethinyl estradiol, drospirenone",
    "clomiphene citrate, gonadotropins",
    "clomiphene citrate, metformin, highly purified urinary fsh",
    "clomiphene citrate, metformin, metformin",
    "clomiphene citrate ( clomid 50 mg )",
    "a combination of metformin",
    "myo-inositol,alpha-lipoic acid",
    "acetyl-l-carnitin, l arginine, co-q10",
    "rhizoma coptidis, radix astragali",
    "flos lonicerae, ophiopogonis radix",
    "silibinin (100 or 200 mg/kg ip)",  # animal dose
}

# ─────────────────────────────────────────────────
# 2. RECLASSIFY: entity_type corrections
# ─────────────────────────────────────────────────

RECLASSIFY = {
    # diagnostic_test
    "transvaginal ultrasound": "diagnostic_test",
    "transvaginal ultrasound examination": "diagnostic_test",
    "transvaginal ultrasound scanning": "diagnostic_test",
    "three-dimensional ultrasound of the female reproductive organ": "diagnostic_test",
    "three dimensional power doppler": "diagnostic_test",
    "abdominal ultra sound": "diagnostic_test",
    "pelvic ultrasound": "diagnostic_test",
    "diagnostic ultrasound": "diagnostic_test",
    "ultrasound scanning": "diagnostic_test",
    "3-d ultrasound": "diagnostic_test",
    "dexa scan": "diagnostic_test",
    "dual-energy x-ray absorptiometry (dexa scan)": "diagnostic_test",
    "total body dual-energy x-ray absorptiometry": "diagnostic_test",
    "mri": "diagnostic_test",
    "mri of liver": "diagnostic_test",
    "mri pdff": "diagnostic_test",
    "functional mri": "diagnostic_test",
    "1h-magnetic resonance spectroscopy": "diagnostic_test",
    "magnetic resonance (mr) assessment of the abdomen": "diagnostic_test",
    "mr assessment of whole body fat": "diagnostic_test",
    "ct scans": "diagnostic_test",
    "pet scan": "diagnostic_test",
    "optic coherence tomography": "diagnostic_test",
    "optical coherence tomography angiography": "diagnostic_test",
    "24-hour ambulatory blood pressure monitoring": "diagnostic_test",
    "hysterosalpingography": "diagnostic_test",
    "fibroscan": "diagnostic_test",
    "fibroscan® (echosens, paris, france)": "diagnostic_test",
    "sonographic studies": "diagnostic_test",
    "doppler evaluation": "diagnostic_test",
    "three dimensional power doppler": "diagnostic_test",
    "gastric emptying scintigraphy": "diagnostic_test",
    "oral glucose tolerance test": "diagnostic_test",
    "oral glucose tolerance test (ogtt)": "diagnostic_test",
    "frequently sampled intravenous glucose tolerance test (fsivgtt)": "diagnostic_test",
    "acoustic analysis by mdvp": "diagnostic_test",
    "dsm-5 diagnostic criteria for asd": "diagnostic_test",
    "raman spectrum": "diagnostic_test",
    "standardized diagnostic": "diagnostic_test",
    "phenotype/genotype assessment": "diagnostic_test",
    "screening for obstructive sleep apnea": "diagnostic_test",

    # comorbidity
    "obesity": "comorbidity",
    "fibrosis": "comorbidity",
    "endometrial hyperplasia": "comorbidity",
    "endometrial hyperplasia (eh)": "comorbidity",
    "gut microbiota dysbiosis": "comorbidity",
    "increased oxidative stress": "comorbidity",
    "hyperandrogenism": "phenotype",
    "weight gain": "comorbidity",

    # phenotype
    "multicystic ovaries.": "phenotype",
    "polycystic ovary morphology": "phenotype",
    "clinical hyperandrogenism": "phenotype",
    "hiperandrogenism": "phenotype",
}

# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────

def run(preview: bool):
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    # Load current entities
    rows = conn.execute(
        "SELECT entity_id, canonical_name, entity_type FROM entity"
    ).fetchall()
    entity_map = {r[1].strip().lower(): (r[0], r[2]) for r in rows}

    to_delete_ids = []
    to_delete_names = []
    reclassify_ops = []

    # Match exact deletes
    for name in DELETE_EXACT:
        key = name.strip().lower()
        if key in entity_map:
            eid, etype = entity_map[key]
            to_delete_ids.append(eid)
            to_delete_names.append(f"  DEL  [{eid:4d}] {name} ({etype})")

    # Match reclassifications
    for name, new_type in RECLASSIFY.items():
        key = name.strip().lower()
        if key in entity_map:
            eid, old_type = entity_map[key]
            if old_type != new_type:
                reclassify_ops.append((eid, name, old_type, new_type))

    print(f"\n{'='*60}")
    print(f"CLEANUP PREVIEW" if preview else "CLEANUP EXECUTE")
    print(f"{'='*60}")
    print(f"Total entities in DB : {len(rows)}")
    print(f"Entities to DELETE   : {len(to_delete_ids)}")
    print(f"Entities to RECLASSIFY: {len(reclassify_ops)}")

    print(f"\n--- DELETES ({len(to_delete_ids)}) ---")
    for line in sorted(to_delete_names):
        print(line)

    print(f"\n--- RECLASSIFY ({len(reclassify_ops)}) ---")
    for eid, name, old_t, new_t in sorted(reclassify_ops, key=lambda x: x[1]):
        print(f"  RECLASSIFY [{eid:4d}] {name}: {old_t} -> {new_t}")

    if preview:
        print("\n[PREVIEW MODE] No changes written. Run with --execute to apply.")
        conn.close()
        return

    # ── Execute deletes ──
    print(f"\nDeleting {len(to_delete_ids)} entities + cascade links...")
    if to_delete_ids:
        placeholders = ",".join("?" * len(to_delete_ids))
        conn.execute(
            f"DELETE FROM article_entity_links WHERE entity_id IN ({placeholders})",
            to_delete_ids,
        )
        conn.execute(
            f"DELETE FROM intervention_signals WHERE entity_id IN ({placeholders})",
            to_delete_ids,
        )
        conn.execute(
            f"DELETE FROM entity WHERE entity_id IN ({placeholders})",
            to_delete_ids,
        )

    # ── Execute reclassifications ──
    print(f"Reclassifying {len(reclassify_ops)} entities...")
    for eid, name, old_t, new_t in reclassify_ops:
        conn.execute(
            "UPDATE entity SET entity_type = ? WHERE entity_id = ?",
            (new_t, eid),
        )

    conn.commit()

    # Final count
    remaining = conn.execute("SELECT COUNT(*) FROM entity").fetchone()[0]
    links_remaining = conn.execute("SELECT COUNT(*) FROM article_entity_links").fetchone()[0]
    print(f"\nDone.")
    print(f"Remaining entities       : {remaining}")
    print(f"Remaining entity links   : {links_remaining}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Show changes without writing")
    parser.add_argument("--execute", action="store_true", help="Apply all changes")
    args = parser.parse_args()

    if not args.preview and not args.execute:
        parser.print_help()
        sys.exit(1)

    run(preview=args.preview)
