"""
PCOS Research — Extracción con LLM LOCAL en GPU de Kaggle
=========================================================
Corre un modelo open-source en la GPU de Kaggle (NO usa la API de Gemini → no
le afecta el limit:0 del free tier). Lee el mismo articles_to_extract.jsonl y
produce extractions_output.jsonl con el MISMO formato que el camino Gemini, así
que scripts/import_from_kaggle.py lo importa sin cambios.

MODELO: Qwen/Qwen2.5-7B-Instruct en 4-bit (entra en T4 16GB, bueno en JSON).
SETUP NOTEBOOK KAGGLE:
  - Settings → Accelerator: GPU T4 x1  (o P100)
  - Settings → Internet: ON  (para descargar el modelo de HuggingFace)
  - Adjuntar el dataset con articles_to_extract.jsonl (Add Input)
Resume automático: vuelve a correr y retoma donde lo dejó.
"""

import subprocess, sys
# bitsandbytes para 4-bit; transformers/accelerate suelen venir, los aseguramos.
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "bitsandbytes", "accelerate", "transformers"], check=True)

import json, time, re, os, glob as _glob
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL_4BIT  = "Qwen/Qwen2.5-14B-Instruct"   # si hay T4+ (sm75): 14B en 4-bit (bitsandbytes)
MODEL_FP16  = "Qwen/Qwen2.5-7B-Instruct"    # si hay P100 (sm60): 7B en fp16 (bnb no soporta P100)
OUTPUT_FILE = "/kaggle/working/extractions_output.jsonl"
TEST_N      = 5             # ← PRUEBA: solo N artículos. Pon None para el batch completo.
# Si TEST_IDS tiene IDs, se usan ESOS exactos (set representativo para juzgar calidad).
# Vacíalo ([]) para volver a "los primeros TEST_N del export".
TEST_IDS    = [
    "10.1093/humrep/deae042",      # cohorte adolescentes Rotterdam
    "10.1111/cen.70000",           # AMH sérica en PCOS
    "10.1093/humrep/dead191",      # DNA methylome (mecanístico)
    "10.1186/s13048-023-01295-y",  # androgen receptor CAG repeats (genético)
    "10.3390/nu15030589",          # guías de estilo de vida / nutrición
]
BATCH_SIZE  = 5             # para 14B en T4; baja a 2-3 si hay OOM
MAX_NEW     = 500           # tokens de salida (el JSON cabe de sobra)
MAX_CHARS   = 3500          # recorte del texto de cada artículo

assert torch.cuda.is_available(), "No hay GPU — activa Accelerator GPU en Settings."
cap = torch.cuda.get_device_capability(0)
SM  = cap[0] * 10 + cap[1]
USE_4BIT = SM >= 75   # bitsandbytes 4-bit necesita sm75+ (T4). P100=sm60 → fp16.
MODEL_ID = MODEL_4BIT if USE_4BIT else MODEL_FP16
if not USE_4BIT:
    BATCH_SIZE = min(BATCH_SIZE, 2)   # fp16 7B en 16GB → batch pequeño
print(f"GPU: {torch.cuda.get_device_name(0)}  (sm_{SM})")
print(f"Modo: {'4-bit / ' + MODEL_4BIT if USE_4BIT else 'fp16 / ' + MODEL_FP16}  | BATCH_SIZE={BATCH_SIZE}")

# ── Localizar el JSONL de artículos en /kaggle/input/ ─────────────────────────
print("\nContenido de /kaggle/input/:")
for f in sorted(_glob.glob("/kaggle/input/**/*", recursive=True))[:40]:
    size = os.path.getsize(f) if os.path.isfile(f) else 0
    print(f"  {f}  ({size/1e6:.1f}MB)" if size else f"  {f}/")

INPUT_FILE = None
for cand in _glob.glob("/kaggle/input/**/*.jsonl", recursive=True):
    if "articles_to_extract" in cand or "pcos" in cand.lower():
        INPUT_FILE = cand
        break
if INPUT_FILE is None:
    jsonls = _glob.glob("/kaggle/input/**/*.jsonl", recursive=True)
    INPUT_FILE = jsonls[0] if jsonls else None
if INPUT_FILE is None:
    raise FileNotFoundError("No se encontró articles_to_extract.jsonl en /kaggle/input/")
print(f"\nArtículos desde: {INPUT_FILE}")

# ── Prompt (schema v1.3 — idéntico al camino Gemini) ──────────────────────────
SYSTEM = """You are a biomedical extraction model for PCOS research.
RULES:
- Return ONLY valid JSON. No markdown. No explanation outside the JSON.
- null > invented value. When unsure -> null.
- effect_direction for HUMAN outcomes only. Animal/in-vitro -> "unclear".
- favorable = primary endpoints significantly improved vs comparator."""

JSON_TEMPLATE = """{
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
  "mechanisms": [{"source":"X","relation":"inhibits|reduces|increases|activates|improves|associated_with","target":"Y","confidence":0.7}],
  "reasoning_summary": "why this effect_direction"
}"""

def user_msg(a: dict) -> str:
    return (f"Title: {a.get('title','')}\n"
            f"Year: {a.get('year','')} | Journal: {a.get('journal','')} | "
            f"Type: {a.get('study_type_llm','')}\n\n"
            f"{(a.get('combined_text','') or '')[:MAX_CHARS]}\n\n"
            f"Return JSON:\n{JSON_TEMPLATE}")

def parse_json(raw: str):
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        i, j = raw.find("{"), raw.rfind("}")     # rescatar el bloque {...}
        if i != -1 and j != -1 and j > i:
            try:
                return json.loads(raw[i:j+1])
            except json.JSONDecodeError:
                return None
        return None

# ── Cargar modelo en 4-bit ────────────────────────────────────────────────────
print(f"\nCargando {MODEL_ID} ({'4-bit' if USE_4BIT else 'fp16'})...")
tok = AutoTokenizer.from_pretrained(MODEL_ID)
tok.padding_side = "left"                          # decoder-only → left padding
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
if USE_4BIT:
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16,
                             bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb, device_map="cuda", dtype=torch.float16)
else:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, device_map="cuda", dtype=torch.float16)
model.eval()
print("Modelo listo.")

# ── Cargar artículos + resume ─────────────────────────────────────────────────
articles = [json.loads(l) for l in open(INPUT_FILE, encoding="utf-8") if l.strip()]
done = set()
if Path(OUTPUT_FILE).exists():
    for l in open(OUTPUT_FILE, encoding="utf-8"):
        try: done.add(json.loads(l)["canonical_id"])
        except: pass
pending = [a for a in articles if a.get("canonical_id") not in done]
print(f"Totales: {len(articles)} | Ya hechos: {len(done)} | Pendientes: {len(pending)}")
if TEST_IDS:
    idset = set(TEST_IDS)
    pending = [a for a in pending if a.get("canonical_id") in idset]
    print(f">>> MODO PRUEBA: {len(pending)} artículos fijados por TEST_IDS")
elif TEST_N:
    pending = pending[:TEST_N]
    print(f">>> MODO PRUEBA: solo {len(pending)} artículos (TEST_N={TEST_N})")

def build_prompt(a: dict) -> str:
    return tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user",   "content": user_msg(a)}],
        tokenize=False, add_generation_prompt=True)

# ── Loop por lotes (escribe incremental para resume) ──────────────────────────
ok = fail = 0
t0 = time.time()
with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
    for s in range(0, len(pending), BATCH_SIZE):
        batch   = pending[s:s + BATCH_SIZE]
        prompts = [build_prompt(a) for a in batch]
        enc = tok(prompts, return_tensors="pt", padding=True,
                  truncation=True, max_length=4096).to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False,
                                  pad_token_id=tok.pad_token_id)
        gen = gen[:, enc["input_ids"].shape[1]:]   # quitar el prompt
        texts = tok.batch_decode(gen, skip_special_tokens=True)

        for a, txt in zip(batch, texts):
            parsed = parse_json(txt)
            if parsed:
                parsed["canonical_id"]      = a["canonical_id"]
                parsed["extraction_status"] = "ollama_generated"
                out.write(json.dumps(parsed, ensure_ascii=False) + "\n")
                ok += 1
            else:
                fail += 1
        out.flush()

        n = ok + fail
        rate = n / (time.time() - t0) * 60
        eta  = (len(pending) - n) / rate if rate else 0
        print(f"[{n}/{len(pending)}] OK={ok} FAIL={fail} | {rate:.1f} art/min | ETA {eta:.0f} min")

elapsed = time.time() - t0
per_art = elapsed / max(ok + fail, 1)
total   = len(done) + ok
print(f"\n{'='*55}\nSesión: {ok} extraídos | {fail} fallos | {elapsed:.0f}s ({elapsed/60:.1f} min)")
print(f"Velocidad: {per_art:.1f}s/artículo  ({60/per_art:.1f} art/min)")
print(f"\nEXTRAPOLACIÓN (a este ritmo):")
print(f"  2.000 artículos  → {per_art*2000/3600:.1f} h")
print(f"  10.653 artículos → {per_art*10653/3600:.1f} h  (~{per_art*10653/3600/9:.1f} sesiones de 9h)")
print(f"\nTotal acumulado en DB-export: {total}/{len(articles)}")
print("Descarga extractions_output.jsonl del Output y pásamelo para revisar calidad.")
