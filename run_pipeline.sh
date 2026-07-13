#!/bin/zsh
# Orquestador PCOS: labeling -> (prep re-extracción v1.1) -> extracción -> normalizer.
# Chunks de 500 con commit por chunk (durable + reanudable). NO incluye anomaly scan.
cd "/Users/elenamaza/Desktop/GITHUB/PROYECTOS CS-MEDICINA/PROYECTO PCOS/" || exit 1
PY=./.venv-mac/bin/python3
DB=data/processed/pcos_research.db
LOG=/tmp/pcos_pipeline.log
QLOG=/tmp/pcos_quality_timeline.log
: > "$QLOG"

say(){ echo "[$(date +%H:%M)] $*" | tee -a "$LOG" "$QLOG"; }
remlabel(){ $PY -c "import sqlite3;c=sqlite3.connect('$DB');print(c.execute(\"SELECT COUNT(*) FROM articles WHERE llm_ready=1 AND canonical_id NOT IN (SELECT canonical_id FROM article_llm_labels WHERE labeling_status='ollama_labeled')\").fetchone()[0])" 2>/dev/null; }
remextract(){ $PY -c "import sqlite3;c=sqlite3.connect('$DB');print(c.execute(\"SELECT COUNT(*) FROM articles WHERE abstract_text IS NOT NULL AND canonical_id NOT IN (SELECT canonical_id FROM article_extractions WHERE extraction_status='ollama_generated')\").fetchone()[0])" 2>/dev/null; }

say "===== PIPELINE START ====="

# ---------- PHASE 1: LABELING ----------
say "PHASE 1 LABELING — pendientes: $(remlabel)"
prev=99999999
for i in $(seq 1 30); do
  r=$(remlabel)
  [ "$r" = "0" ] && { say "  labeling completo"; break; }
  if [ "$r" -ge "$prev" ]; then say "  labeling sin progreso (rem=$r) — paro fase"; break; fi
  prev=$r
  say "  labeling chunk $i (rem=$r)"
  $PY scripts/run_ollama_article_labeling.py --top-k 500 --model gemini-2.5-flash-lite >> "$LOG" 2>&1
  $PY quality_monitor.py 2>/dev/null | grep -E "LABELING|total=|utility:|study_type:" >> "$QLOG"
done
say "PHASE 1 DONE — labeling pendientes: $(remlabel)"

# ---------- PHASE 2: PREP RE-EXTRACCIÓN v1.1 ----------
say "PHASE 2 PREP — borrando extracciones v1.1 (se re-extraerán a v1.3)"
$PY -c "
import sqlite3
c=sqlite3.connect('$DB')
n=c.execute(\"SELECT COUNT(*) FROM article_extractions WHERE prompt_version LIKE 'schema-1.1%'\").fetchone()[0]
c.execute(\"DELETE FROM mechanism_links WHERE canonical_id IN (SELECT canonical_id FROM article_extractions WHERE prompt_version LIKE 'schema-1.1%')\")
c.execute(\"DELETE FROM article_extractions WHERE prompt_version LIKE 'schema-1.1%'\")
c.commit()
print(f'  borradas {n} extracciones v1.1 -> ahora pendientes')
" | tee -a "$LOG" "$QLOG"

# ---------- PHASE 3: EXTRACCIÓN ----------
say "PHASE 3 EXTRACTION — pendientes: $(remextract)"
prev=99999999
for i in $(seq 1 20); do
  r=$(remextract)
  [ "$r" = "0" ] && { say "  extracción completa"; break; }
  if [ "$r" -ge "$prev" ]; then say "  extracción sin progreso (rem=$r) — paro fase"; break; fi
  prev=$r
  say "  extraction chunk $i (rem=$r)"
  $PY scripts/run_ollama_extraction.py --top-k 500 --model gemini-2.5-flash-lite >> "$LOG" 2>&1
  $PY quality_monitor.py 2>/dev/null | grep -E "EXTRACTION|total=|intervention|effect_direction" >> "$QLOG"
done
say "PHASE 3 DONE — extraction pendientes: $(remextract)"

# ---------- PHASE 4: NORMALIZER ----------
say "PHASE 4 NORMALIZER — corriendo entity_normalizer.py"
$PY scripts/entity_normalizer.py >> "$LOG" 2>&1 && say "PHASE 4 DONE" || say "PHASE 4 ERROR (ver $LOG)"

say "===== PIPELINE COMPLETE (hasta normalizer; anomaly scan = manual) ====="
