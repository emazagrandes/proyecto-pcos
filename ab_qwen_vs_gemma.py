"""
A/B local: Qwen2.5-14B (Ollama) vs baseline Gemma4:31b — mismos artículos,
mismo prompt (schema-1.3) y mismo input que vio Gemma. Compara campo a campo.

Uso:  ./.venv-mac/bin/python3 ab_qwen_vs_gemma.py
"""
import os, sys, json, re, sqlite3, time

# Backend configurable por env (default Ollama+Qwen). Para Gemini:
#   LLM_BACKEND=gemini GEMINI_MODEL=gemini-2.5-flash ./.venv-mac/bin/python3 ab_qwen_vs_gemma.py
os.environ.setdefault("LLM_BACKEND", "ollama")
os.environ.setdefault("OLLAMA_GENERATE_MODEL", "qwen2.5:14b")
CHALLENGER = (os.environ.get("GEMINI_MODEL") if os.environ.get("LLM_BACKEND") == "gemini"
              else os.environ.get("OLLAMA_GENERATE_MODEL"))
sys.path.insert(0, "scripts")

from llm_support import build_extraction_prompt, SYSTEM_PROMPT   # noqa: E402
from llm_client import chat as llm_chat                          # noqa: E402

DB = "data/processed/pcos_research.db"
IDS = [
    "10.1210/clinem/dgac294",       # sleeve gastrectomy — favorable (cirugía)
    "10.3389/fcell.2021.647522",    # ADAMTS1 siRNA — unclear (in-vitro/mecanístico)
    "10.1016/j.heliyon.2023.e13024",# ovulation induction — mixed
    "10.1186/s12986-021-00586-9",   # melatonina combinada — favorable (combo)
    "10.1038/s41598-025-33836-4",   # exposición a PFAS — unclear (ambiental)
]
FIELDS = ["intervention", "comparator", "effect_direction", "n_total",
          "population_bmi", "population_ethnicity", "population_age_range",
          "main_outcomes", "limitations", "notable_finding", "reasoning_summary"]


def strip_json(t: str) -> str:
    t = re.sub(r"^```(?:json)?\s*", "", t.strip())
    t = re.sub(r"\s*```$", "", t).strip()
    i, j = t.find("{"), t.rfind("}")
    return t[i:j+1] if i != -1 and j != -1 else t


def short(v, n=110):
    if v is None:
        return "—"
    if isinstance(v, (list, dict)):
        v = json.dumps(v, ensure_ascii=False)
    v = str(v).replace("\n", " ")
    return v if len(v) <= n else v[:n] + "…"


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

for cid in IDS:
    base = conn.execute("SELECT * FROM article_extractions WHERE canonical_id=?", (cid,)).fetchone()
    if not base:
        print(f"\n### {cid} — SIN baseline, salto\n"); continue
    payload = json.loads(base["source_payload"])
    ft = conn.execute("""SELECT abstract_full, methods_text, results_text,
                                discussion_text, fetch_source
                         FROM article_fulltexts WHERE canonical_id=?""", (cid,)).fetchone()
    fulltext = None
    if ft and ft["fetch_source"]:
        fulltext = {k: ft[k] for k in ("abstract_full", "methods_text",
                                       "results_text", "discussion_text", "fetch_source")}
    prompt = build_extraction_prompt(payload, fulltext=fulltext)

    t0 = time.time()
    raw = llm_chat([{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}],
                   temperature=0.0, max_tokens=1200)
    dt = time.time() - t0
    try:
        q = json.loads(strip_json(raw))
    except Exception as e:
        q = {"_PARSE_ERROR": str(e), "_raw": raw[:300]}

    print(f"\n{'='*90}\n### {cid}   ({payload.get('title','')[:70]})   [{dt:.0f}s]")
    print(f"{'campo':<22}{'GEMMA (baseline)':<46}{CHALLENGER}")
    print("-" * 90)
    for f in FIELDS:
        print(f"{f:<22}{short(base[f] if f in base.keys() else None, 44):<46}{short(q.get(f), 44)}")
    if "_PARSE_ERROR" in q:
        print(f"  ⚠️ QWEN no devolvió JSON válido: {q['_PARSE_ERROR']}")
    print(f"mechanisms (qwen): {short(q.get('mechanisms'), 80)}")

conn.close()
print(f"\n{'='*90}\nListo.")
