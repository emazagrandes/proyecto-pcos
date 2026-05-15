import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests

from config import BASE_QUERY, PUBMED_FETCH_URL, PUBMED_SEARCH_URL, PUBMED_SUMMARY_URL, RAW_DIR


def _json_payload(response: requests.Response) -> dict:
    return json.loads(response.text, strict=False)


def _fetch_abstract_map(pmids: list[str]) -> dict[str, str | None]:
    if not pmids:
        return {}
    resp = requests.get(
        PUBMED_FETCH_URL,
        params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"},
        timeout=60,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    abstract_map: dict[str, str | None] = {pmid: None for pmid in pmids}

    for article in root.findall('.//PubmedArticle'):
        pmid_node = article.find('.//MedlineCitation/PMID')
        if pmid_node is None or not pmid_node.text:
            continue
        pmid = pmid_node.text.strip()
        abstract_parts = []
        for node in article.findall('.//Abstract/AbstractText'):
            label = node.attrib.get('Label')
            text = ''.join(node.itertext()).strip()
            if not text:
                continue
            abstract_parts.append(f"{label}: {text}" if label else text)
        abstract_map[pmid] = ' '.join(abstract_parts) if abstract_parts else None
    return abstract_map


def fetch_pubmed(days_back: int = 60, retmax: int = 0, batch_size: int = 200,
                 query: str | None = None, out_file: str | None = None) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / (out_file if out_file else "pubmed_articles.jsonl")

    mindate = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    maxdate = datetime.utcnow().strftime("%Y/%m/%d")

    active_query = query if query else BASE_QUERY

    search_params = {
        "db": "pubmed",
        "term": active_query,
        "retmode": "json",
        "retmax": 0,
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",
        "usehistory": "y",
    }

    search_resp = requests.get(PUBMED_SEARCH_URL, params=search_params, timeout=45)
    search_resp.raise_for_status()
    search_result = _json_payload(search_resp).get("esearchresult", {})
    total_count = int(search_result.get("count", 0))
    webenv = search_result.get("webenv")
    query_key = search_result.get("querykey")

    if not total_count or not webenv or not query_key:
        out_path.write_text("", encoding="utf-8")
        return out_path

    max_records = total_count if retmax <= 0 else min(retmax, total_count)

    with out_path.open("w", encoding="utf-8") as f:
        for retstart in range(0, max_records, batch_size):
            current_batch_size = min(batch_size, max_records - retstart)
            summary_params = {
                "db": "pubmed",
                "query_key": query_key,
                "WebEnv": webenv,
                "retstart": retstart,
                "retmax": current_batch_size,
                "retmode": "json",
            }
            summary_resp = requests.get(PUBMED_SUMMARY_URL, params=summary_params, timeout=45)
            summary_resp.raise_for_status()
            summary_data = _json_payload(summary_resp).get("result", {})
            pmids = summary_data.get("uids", [])
            abstract_map = _fetch_abstract_map(pmids)

            for pmid in pmids:
                item = summary_data.get(pmid, {})
                record = {
                    "source": "pubmed",
                    "source_id": pmid,
                    "title": item.get("title"),
                    "pubdate": item.get("pubdate"),
                    "fulljournalname": item.get("fulljournalname"),
                    "authors": [a.get("name") for a in item.get("authors", []) if a.get("name")],
                    "articleids": item.get("articleids", []),
                    "doi": next(
                        (aid.get("value") for aid in item.get("articleids", []) if aid.get("idtype") == "doi"),
                        None,
                    ),
                    "abstract_text": abstract_map.get(pmid),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=60)
    parser.add_argument("--retmax", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--query", type=str, default=None,
                        help="Query personalizada (sobreescribe BASE_QUERY)")
    parser.add_argument("--out-file", type=str, default=None,
                        help="Nombre del archivo de salida en data/raw/")
    args = parser.parse_args()

    path = fetch_pubmed(days_back=args.days_back, retmax=args.retmax,
                        batch_size=args.batch_size, query=args.query,
                        out_file=args.out_file)
    print(f"PubMed saved: {path}")
