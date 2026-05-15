param(
    [int]$LabelBatch  = 500,
    [int]$ExtractBatch = 500
)

$base    = "C:\Users\emaza\OneDrive\Escritorio\CODEX\PRUEBA1"
$python  = "$base\.venv\Scripts\python.exe"
$logFile = "$base\reports\pipeline_clock.log"
$env:PYTHONIOENCODING = 'utf-8'

Start-Transcript -Path $logFile -Append -Force | Out-Null

function Log($msg) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" }

Log "============================================"
Log "INICIO PIPELINE CLOCK"
Log "  label_batch=$LabelBatch  extract_batch=$ExtractBatch"
Log "============================================"

# ── PASO 1: LABELING ─────────────────────────────────────────────────────────
Log "[1/3] Lanzando labeling --top-k $LabelBatch ..."
& $python "$base\scripts\run_ollama_article_labeling.py" --top-k $LabelBatch
$exitLabel = $LASTEXITCODE
Log "[1/3] Labeling terminado — exit code: $exitLabel"

if ($exitLabel -ne 0) {
    Log "[1/3] ERROR en labeling (codigo $exitLabel) — abortando pipeline."
    Stop-Transcript | Out-Null
    [System.Environment]::Exit($exitLabel)
}

# ── PASO 2: EXTRACTION ───────────────────────────────────────────────────────
Log "[2/3] Lanzando extraction --top-k $ExtractBatch ..."
& $python "$base\scripts\run_ollama_extraction.py" --top-k $ExtractBatch
$exitExtract = $LASTEXITCODE
Log "[2/3] Extraction terminado — exit code: $exitExtract"

if ($exitExtract -ne 0) {
    Log "[2/3] ERROR en extraction (codigo $exitExtract) — abortando pipeline."
    Stop-Transcript | Out-Null
    [System.Environment]::Exit($exitExtract)
}

# ── PASO 3: ENTITY NORMALIZER ────────────────────────────────────────────────
Log "[3/3] Lanzando entity_normalizer ..."
& $python "$base\scripts\entity_normalizer.py"
$exitNorm = $LASTEXITCODE
Log "[3/3] Entity normalizer terminado — exit code: $exitNorm"

Log "============================================"
Log "PIPELINE COMPLETO — label=$exitLabel extract=$exitExtract normalizer=$exitNorm"
Log "============================================"

Stop-Transcript | Out-Null
[System.Environment]::Exit($exitNorm)
