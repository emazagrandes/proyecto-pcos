"""
PCOS Research — Extracción via Gemini API en Kaggle
=====================================================
No necesita GPU. No necesita modelos descargados.
Modelo: gemini-2.0-flash (generoso en quota gratuita)
Velocidad: ~500-800 artículos por sesión.
Resume automáticamente — corre hasta completar los 2000.
"""

import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-generativeai"], check=True)

import json, time, re, os, glob as _glob
from pathlib import Path
import google.generativeai as genai

# La clave se lee del entorno. En Kaggle: Add-ons → Secrets → GEMINI_API_KEY,
# o define la variable de entorno antes de ejecutar. NUNCA hardcodear la clave.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise SystemExit("Falta GEMINI_API_KEY en el entorno (Kaggle Secrets o variable de entorno).")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

OUTPUT_FILE = "/kaggle/working/extractions_output.jsonl"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)
print(f"Gemini OK | modelo: {GEMINI_MODEL}")

# ── Debug: ver qué hay en /kaggle/input/ ──────────────────────────────────────
print("\nContenido de /kaggle/input/:")
all_files = _glob.glob("/kaggle/input/**/*", recursive=True)
if all_files:
    for f in sorted(all_files)[:40]:
        size = os.path.getsize(f) if os.path.isfile(f) else 0
        print(f"  {f}  ({size/1e6:.1f}MB)" if size else f"  {f}/")
else:
    print("  (vacío — dataset no montado)")

# Auto-detectar el JSONL de artículos
INPUT_FILE = None
for candidate in _glob.glob("/kaggle/input/**/*.jsonl", recursive=True):
    if "articles_to_extract" in candidate or "pcos" in candidate.lower():
        INPUT_FILE = candidate
        break
if INPUT_FILE is None:
    jsonls = _glob.glob("/kaggle/input/**/*.jsonl", recursive=True)
    if jsonls:
        INPUT_FILE = jsonls[0]

print(f"\nArchivo de artículos: {INPUT_FILE}")
if INPUT_FILE is None:
    raise FileNotFoundError(
        "No se encontró articles_to_extract.jsonl en /kaggle/input/\n"
        "Verifica que el dataset elenamazagrandes/pcos-articles-extraction "
        "esté adjunto al notebook."
    )

SYSTEM = """You are a biomedical extraction model for PCOS research.
RULES:
- Return ONLY valid JSON. No markdown. No explanation outside the JSON.
- null > invented value. When unsure → null.
- effect_direction for HUMAN outcomes only. Animal/in-vitro → "unclear".
- favorable = primary endpoints significantly improved vs comparator."""

def make_prompt(a: dict) -> str:
    return f"""{SYSTEM}

Title: {a.get("title","")}
Year: {a.get("year","")} | Journal: {a.get("journal","")} | Type: {a.get("study_type_llm","")}

{a.get("combined_text","")[:3000]}

Return JSON:
{{
  "schema_version": "1.3",
  "intervention": "main treatment",
  "comparator": "control group or null",
  "dose": "dose/frequency or null",
  "effect_direction": "favorable|unfavorable|neutral|mixed|unclear",
  "n_total": null,
  "main_outcomes": ["outcome1"],
  "limitations": ["limit1"],
  "population": "one sentence: condition, n, BMI, age, country",
  "population_diet": null,
  "population_bmi": "obese|overweight|lean|mixed BMI|null",
  "population_age_range": null,
  "population_comorbidities": [],
  "population_ethnicity": "inferred from location",
  "notable_finding": null,
  "mechanisms": [{{"source":"X","relation":"inhibits|reduces|increases|activates|improves|associated_with","target":"Y","confidence":0.7}}],
  "reasoning_summary": "why this effect_direction"
}}"""

def extract_one(article: dict) -> tuple[dict | None, int]:
    """Returns (result, tokens_used)"""
    for attempt in range(3):
        try:
            resp = model.generate_content(
                make_prompt(article),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=500,
                )
            )
            raw = resp.text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            parsed = json.loads(raw)
            parsed["canonical_id"]      = article["canonical_id"]
            parsed["extraction_status"] = "ollama_generated"
            # Estimate tokens (Gemini doesn't always return usage)
            tokens = getattr(resp.usage_metadata, "total_token_count", 900) if hasattr(resp, "usage_metadata") else 900
            return parsed, tokens
        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(1)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                wait = 60 * (attempt + 1)
                print(f"  Rate limit — esperando {wait}s...")
                time.sleep(wait)
            elif "500" in err or "503" in err:
                time.sleep(5 * (attempt + 1))
            elif attempt < 2:
                time.sleep(2)
            else:
                print(f"  Error en {article.get('canonical_id','?')}: {err[:100]}")
                return None, 0
    return None, 0

# Cargar artículos
articles = [json.loads(l) for l in open(INPUT_FILE, encoding="utf-8") if l.strip()]
print(f"Artículos totales: {len(articles)}")

# Resume automático
done_ids = set()
if Path(OUTPUT_FILE).exists():
    for l in open(OUTPUT_FILE, encoding="utf-8"):
        try: done_ids.add(json.loads(l)["canonical_id"])
        except: pass
pending = [a for a in articles if a["canonical_id"] not in done_ids]
print(f"Ya procesados: {len(done_ids)} | Pendientes esta sesión: {len(pending)}")

# Loop
ok = fail = tokens_used = 0
t_start = time.time()

with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
    for i, article in enumerate(pending):
        result, tkns = extract_one(article)
        tokens_used += tkns

        if result:
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()
            ok += 1
        else:
            fail += 1

        if (ok + fail) % 25 == 0 and (ok + fail) > 0:
            elapsed = time.time() - t_start
            rate    = (ok + fail) / elapsed * 3600
            eta_h   = (len(pending) - i - 1) / (rate / 3600) if rate > 0 else 0
            print(f"[{ok+fail}/{len(pending)}] OK={ok} FAIL={fail} | "
                  f"{rate:.0f} art/h | ETA {eta_h:.1f}h | tokens ~{tokens_used:,}")

        time.sleep(0.1)

total = len(done_ids) + ok
elapsed_h = (time.time() - t_start) / 3600
print(f"\n{'='*55}")
print(f"Sesión: {ok} extraídos | {fail} fallos | {elapsed_h:.1f}h")
print(f"Total acumulado: {total}/{len(articles)}")
print(f"Tokens estimados: {tokens_used:,}")
if total >= len(articles):
    print("TODOS PROCESADOS — descarga extractions_output.jsonl del Output")
else:
    days_left = (len(articles) - total) / max(ok, 1)
    print(f"~{days_left:.0f} sesión(es) más — vuelve a correr mañana")
    print("   (el notebook retoma automáticamente donde lo dejó)")
