import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

from config import PUBMED_FETCH_URL, RAW_DIR


BATCH_SIZE = 100


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


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
    abstract_map = {pmid: None for pmid in pmids}
    for article in root.findall('.//PubmedArticle'):
        pmid_node = article.find('.//MedlineCitation/PMID')
        if pmid_node is None or not pmid_node.text:
            continue
        pmid = pmid_node.text.strip()
        parts = []
        for node in article.findall('.//Abstract/AbstractText'):
            label = node.attrib.get('Label')
            text = ''.join(node.itertext()).strip()
            if not text:
                continue
            parts.append(f"{label}: {text}" if label else text)
        abstract_map[pmid] = ' '.join(parts) if parts else None
    return abstract_map


def enrich_pubmed_abstracts() -> Path:
    path = RAW_DIR / "pubmed_articles.jsonl"
    rows = _load_jsonl(path)
    missing_pmids = [row.get("source_id") for row in rows if row.get("source") == "pubmed" and not row.get("abstract_text") and row.get("source_id")]
    for start in range(0, len(missing_pmids), BATCH_SIZE):
        batch = missing_pmids[start:start + BATCH_SIZE]
        abstract_map = _fetch_abstract_map(batch)
        for row in rows:
            pmid = row.get("source_id")
            if pmid in abstract_map and not row.get("abstract_text"):
                row["abstract_text"] = abstract_map[pmid]
    _write_jsonl(path, rows)
    return path


if __name__ == "__main__":
    output_path = enrich_pubmed_abstracts()
    print(f"PubMed abstracts enriched: {output_path}")
