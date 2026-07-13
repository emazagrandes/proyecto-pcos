"""
quality_monitor.py — Vigila la calidad de lo que produce gemini-2.5-flash-lite
mientras corren labeling/extracción. Solo lectura sobre la DB (WAL → seguro
mientras otro proceso escribe).
Uso:  ./.venv-mac/bin/python3 quality_monitor.py
"""
import sqlite3, collections
DB = "data/processed/pcos_research.db"
TAG = "%flash-lite%"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row


def dist(rows, key):
    cnt = collections.Counter((r[key] or "NULL") for r in rows)
    return ", ".join(f"{k}:{v}" for k, v in cnt.most_common(8))


# ---------- LABELING ----------
lab = c.execute("SELECT * FROM article_llm_labels WHERE labeler_name LIKE ? ORDER BY rowid DESC LIMIT 300", (TAG,)).fetchall()
ntot = c.execute("SELECT COUNT(*) FROM article_llm_labels WHERE labeler_name LIKE ?", (TAG,)).fetchone()[0]
print(f"\n=== LABELING (flash-lite) ===  total={ntot}")
if lab:
    us = [r["utility_score_llm"] for r in lab if r["utility_score_llm"] is not None]
    nullst = sum(1 for r in lab if not r["study_type_llm"])
    print(f"  (últimos {len(lab)}) utility: min={min(us):.2f} mean={sum(us)/len(us):.2f} max={max(us):.2f} | %util>=0.4={100*sum(u>=0.4 for u in us)/len(us):.0f}%")
    print(f"  study_type: {dist(lab,'study_type_llm')}")
    print(f"  evidence_tier: {dist(lab,'evidence_tier_llm')}")
    print(f"  study_type NULL: {nullst}/{len(lab)}")

# ---------- EXTRACTION ----------
ext = c.execute("SELECT * FROM article_extractions WHERE extractor_name LIKE ? ORDER BY rowid DESC LIMIT 300", (TAG,)).fetchall()
etot = c.execute("SELECT COUNT(*) FROM article_extractions WHERE extractor_name LIKE ?", (TAG,)).fetchone()[0]
print(f"\n=== EXTRACTION (flash-lite) ===  total={etot}")
if ext:
    nint = sum(1 for r in ext if not r["intervention"])
    nnf  = sum(1 for r in ext if not r["notable_finding"])
    print(f"  (últimos {len(ext)}) intervention NULL: {100*nint/len(ext):.0f}%  | notable_finding NULL: {100*nnf/len(ext):.0f}%")
    print(f"  effect_direction: {dist(ext,'effect_direction')}")
c.close()
