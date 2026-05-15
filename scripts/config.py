from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
CLINICALTRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"
OPENALEX_URL = "https://api.openalex.org/works"

BASE_QUERY = (
    '(("polycystic ovary syndrome") OR PCOS OR SOP) '
    'AND (women OR female OR infertility OR ovulation OR hyperandrogenism)'
)
