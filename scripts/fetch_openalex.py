import argparse
import json
from pathlib import Path

import requests

from config import BASE_QUERY, OPENALEX_URL, RAW_DIR


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, word))
    if not positions:
        return None
    positions.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positions)


def fetch_openalex(per_page: int = 100, max_records: int = 0) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "openalex_works.jsonl"

    params = {
        "search": BASE_QUERY,
        "per-page": per_page,
        "sort": "cited_by_count:desc",
        "cursor": "*",
    }

    with out_path.open("w", encoding="utf-8") as f:
        written = 0
        while True:
            resp = requests.get(OPENALEX_URL, params=params, timeout=45)
            resp.raise_for_status()
            payload = resp.json()
            results = payload.get("results", [])

            if not results:
                break

            for work in results:
                primary_location = work.get("primary_location") or {}
                source = primary_location.get("source") or {}
                row = {
                    "source": "openalex",
                    "source_id": work.get("id"),
                    "doi": work.get("doi"),
                    "title": work.get("title"),
                    "year": work.get("publication_year"),
                    "type": work.get("type"),
                    "cited_by_count": work.get("cited_by_count"),
                    "host_venue": source.get("display_name"),
                    "abstract_text": _reconstruct_abstract(work.get("abstract_inverted_index")),
                    "url": work.get("id"),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
                if max_records > 0 and written >= max_records:
                    return out_path

            next_cursor = (payload.get("meta") or {}).get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor

    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-page", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=0)
    args = parser.parse_args()

    path = fetch_openalex(per_page=args.per_page, max_records=args.max_records)
    print(f"OpenAlex saved: {path}")
