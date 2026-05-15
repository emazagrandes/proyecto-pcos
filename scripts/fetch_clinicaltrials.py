import argparse
import json
from pathlib import Path

import requests

from config import CLINICALTRIALS_URL, RAW_DIR


def _study_to_row(study: dict) -> dict:
    proto = study.get("protocolSection", {})
    status = proto.get("statusModule", {})
    ident = proto.get("identificationModule", {})
    design = proto.get("designModule", {})
    cond = proto.get("conditionsModule", {})
    arms = proto.get("armsInterventionsModule", {})
    elig = proto.get("eligibilityModule", {})
    outcomes = proto.get("outcomesModule", {})
    refs = study.get("derivedSection", {}).get("miscInfoModule", {}).get("references", [])

    intervention_names = [
        i.get("name") for i in arms.get("interventions", []) if i.get("name")
    ]
    outcome_measures = [
        o.get("measure") for o in outcomes.get("primaryOutcomes", []) if o.get("measure")
    ]
    publications = [r.get("pmid") for r in refs if r.get("pmid")]

    return {
        "source": "clinicaltrials",
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "phase": ", ".join(design.get("phases", [])) if design.get("phases") else None,
        "conditions": cond.get("conditions", []),
        "interventions": intervention_names,
        "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
        "sex": elig.get("sex"),
        "age": {
            "minimum": elig.get("minimumAge"),
            "maximum": elig.get("maximumAge"),
        },
        "outcome_measures": outcome_measures,
        "has_results": bool(study.get("resultsSection")),
        "results_first_posted": (status.get("resultsFirstPostDateStruct") or {}).get("date"),
        "completion_date": (status.get("completionDateStruct") or {}).get("date"),
        "linked_publications": publications,
        "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}" if ident.get("nctId") else None,
    }


def fetch_trials(query: str = "polycystic ovary syndrome", page_size: int = 100) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "clinical_trials.jsonl"

    params = {
        "query.term": query,
        "pageSize": page_size,
        "format": "json",
    }

    rows = []
    next_token = None

    while True:
        if next_token:
            params["pageToken"] = next_token
        resp = requests.get(CLINICALTRIALS_URL, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()

        studies = payload.get("studies", [])
        rows.extend(_study_to_row(s) for s in studies)

        next_token = payload.get("nextPageToken")
        if not next_token:
            break

    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="polycystic ovary syndrome")
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()

    path = fetch_trials(query=args.query, page_size=args.page_size)
    print(f"Trials saved: {path}")
