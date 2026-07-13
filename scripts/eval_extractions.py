#!/usr/bin/env python3
"""
Accuracy harness: score article_extractions against the human gold set
(article_gold_extractions). This is the yardstick for every extraction change —
run it before and after a prompt/full-text change to prove the delta is real,
not asserted.

Metrics reported:
  effect_direction:
    - overall accuracy (exact match) on the gold set
    - accuracy EXCLUDING gold==unclear (does the model get the DIRECTIONAL cases?)
    - confusion matrix (gold rows x predicted cols)
    - the key failure mode: % of gold-directional rows the model called 'unclear'
      (= the "unclear leak" that the full-text work is meant to reduce)
  intervention:
    - % of gold rows where the model produced a non-empty intervention
    - fuzzy match rate (gold token subset of predicted, case-insensitive)
  n_total:
    - % present, and exact-match rate where gold n_total is known

By default scores the live article_extractions table. Pass --pred-table to score
an alternative table (e.g. a re-extraction written to article_extractions_v2),
so you can A/B two extraction runs against the same gold.

Usage:
  python scripts/eval_extractions.py
  python scripts/eval_extractions.py --pred-table article_extractions_v2 --label "gemini+fulltext"
  python scripts/eval_extractions.py --json eval_baseline.json
"""
from __future__ import annotations
import argparse, json, sqlite3
from collections import Counter, defaultdict
from pathlib import Path

DB_PATH = Path("data/processed/pcos_research.db")
DIRECTIONS = ["favorable", "neutral", "mixed", "unfavorable", "unclear"]


def _norm(s):
    return (s or "").strip().lower()


def load(conn, pred_table):
    gold = {r[0]: dict(effect=_norm(r[1]), interv=_norm(r[2]), n=r[3])
            for r in conn.execute(
        "SELECT canonical_id, gold_effect_direction, gold_intervention, gold_n_total "
        "FROM article_gold_extractions").fetchall()}
    preds = {}
    for cid in gold:
        row = conn.execute(
            f"SELECT effect_direction, intervention, n_total FROM {pred_table} "
            "WHERE canonical_id=?", (cid,)).fetchone()
        if row:
            preds[cid] = dict(effect=_norm(row[0]), interv=_norm(row[1]), n=row[2])
    return gold, preds


def score(gold, preds, label):
    ids = [c for c in gold if c in preds]
    n = len(ids)
    out = {"label": label, "n_gold": len(gold), "n_scored": n}
    if n == 0:
        out["error"] = "no overlap between gold and predictions"
        return out

    # ---- effect_direction ----
    correct = sum(1 for c in ids if gold[c]["effect"] == preds[c]["effect"])
    out["effect_accuracy_overall"] = round(correct / n, 3)

    dir_ids = [c for c in ids if gold[c]["effect"] != "unclear"]
    if dir_ids:
        dcorr = sum(1 for c in dir_ids if gold[c]["effect"] == preds[c]["effect"])
        out["effect_accuracy_directional"] = round(dcorr / len(dir_ids), 3)
        leaked = sum(1 for c in dir_ids if preds[c]["effect"] == "unclear")
        out["unclear_leak_rate"] = round(leaked / len(dir_ids), 3)
        out["n_directional_gold"] = len(dir_ids)

    cm = defaultdict(Counter)
    for c in ids:
        cm[gold[c]["effect"]][preds[c]["effect"]] += 1
    out["confusion_matrix"] = {g: dict(cm[g]) for g in DIRECTIONS if cm[g]}

    # ---- intervention ----
    interv_present = sum(1 for c in ids if preds[c]["interv"])
    out["intervention_present_rate"] = round(interv_present / n, 3)
    gold_interv_ids = [c for c in ids if gold[c]["interv"]]
    if gold_interv_ids:
        fuzzy = 0
        for c in gold_interv_ids:
            g = set(gold[c]["interv"].replace(",", " ").split())
            p = set(preds[c]["interv"].replace(",", " ").split())
            if g and (g <= p or (g & p and len(g & p) / len(g) >= 0.5)):
                fuzzy += 1
        out["intervention_fuzzy_match_rate"] = round(fuzzy / len(gold_interv_ids), 3)
        out["n_intervention_gold"] = len(gold_interv_ids)

    # ---- n_total ----
    n_present = sum(1 for c in ids if preds[c]["n"] is not None)
    out["n_total_present_rate"] = round(n_present / n, 3)
    gold_n_ids = [c for c in ids if gold[c]["n"] is not None]
    if gold_n_ids:
        nmatch = sum(1 for c in gold_n_ids if preds[c]["n"] == gold[c]["n"])
        out["n_total_exact_match_rate"] = round(nmatch / len(gold_n_ids), 3)
        out["n_total_gold_known"] = len(gold_n_ids)
    return out


def pretty(out):
    print(f"\n=== Extraction accuracy vs gold — {out['label']} ===")
    print(f"gold rows: {out['n_gold']} | scored (overlap): {out['n_scored']}")
    if out.get("error"):
        print("  ERROR:", out["error"]); return
    print(f"\neffect_direction:")
    print(f"  overall accuracy      : {out['effect_accuracy_overall']:.1%}")
    if "effect_accuracy_directional" in out:
        print(f"  directional accuracy  : {out['effect_accuracy_directional']:.1%}  "
              f"(on {out['n_directional_gold']} gold non-unclear rows)")
        print(f"  UNCLEAR LEAK rate     : {out['unclear_leak_rate']:.1%}  "
              f"(directional gold that model called 'unclear' — lower is better)")
    print("  confusion (gold row -> predicted):")
    for g, preds in out["confusion_matrix"].items():
        print(f"    {g:12} -> {preds}")
    print(f"\nintervention:")
    print(f"  present rate          : {out['intervention_present_rate']:.1%}")
    if "intervention_fuzzy_match_rate" in out:
        print(f"  fuzzy match vs gold   : {out['intervention_fuzzy_match_rate']:.1%}  "
              f"(on {out['n_intervention_gold']} gold rows)")
    print(f"\nn_total:")
    print(f"  present rate          : {out['n_total_present_rate']:.1%}")
    if "n_total_exact_match_rate" in out:
        print(f"  exact match vs gold   : {out['n_total_exact_match_rate']:.1%}  "
              f"(on {out['n_total_gold_known']} gold rows with known n)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-table", default="article_extractions")
    ap.add_argument("--label", default=None)
    ap.add_argument("--json", default=None, help="write metrics to this JSON file")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    gold, preds = load(conn, args.pred_table)
    out = score(gold, preds, args.label or args.pred_table)
    conn.close()
    pretty(out)
    if args.json:
        json.dump(out, open(args.json, "w"), indent=2)
        print(f"\nwrote {args.json}")
