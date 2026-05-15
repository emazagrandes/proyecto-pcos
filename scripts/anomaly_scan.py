import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


NOISE_INTERVENTIONS = {
    "",
    "no intervention",
    "this study does not involve any interventions",
    "women with polycystic ovary syndrome",
    "incidence",
}
EXCLUDED_SUBSTRINGS = (
    "placebo",
    "follow-up",
    "follow up",
    "oral glucose tolerance test",
    "ogtt",
    "questionnaire",
    "blood draw",
    "biopsy",
    "urine collection",
    "phlebotomy",
    "ultrasound",
    "screening program",
)


def _load_trials(conn: sqlite3.Connection) -> pd.DataFrame:
    try:
        return pd.read_sql_query("SELECT * FROM trials", conn)
    except Exception:
        return pd.DataFrame()


def _parse_listish(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            return [text]
    return [text]


def _normalize_name(value: str) -> str | None:
    text = " ".join(value.lower().split())
    if text in NOISE_INTERVENTIONS:
        return None
    if any(fragment in text for fragment in EXCLUDED_SUBSTRINGS):
        return None
    return text


def anomaly_scan(top_n: int = 25) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROCESSED_DIR / "pcos_research.db"
    out_path = REPORTS_DIR / "latest_trial_signals.md"

    if not db_path.exists():
        out_path.write_text("# Senales en ensayos SOP\n\nNo existe base de datos procesada.\n", encoding="utf-8")
        return out_path

    with sqlite3.connect(db_path) as conn:
        trials = _load_trials(conn)

    if trials.empty:
        out_path.write_text("# Senales en ensayos SOP\n\nNo hay datos de ensayos para analizar.\n", encoding="utf-8")
        return out_path

    trials["enrollment"] = pd.to_numeric(trials.get("enrollment"), errors="coerce")
    trials["has_results"] = trials.get("has_results", False).astype(bool)
    trials["status"] = trials.get("status", "").fillna("")

    normalized = trials.get("normalized_interventions")
    if normalized is None:
        normalized = trials.get("interventions", pd.Series([[] for _ in range(len(trials))]))
    normalized = normalized.map(_parse_listish)

    exploded = trials.assign(normalized_intervention_list=normalized).explode("normalized_intervention_list")
    exploded["normalized_intervention_list"] = exploded["normalized_intervention_list"].fillna("").astype(str)
    exploded["normalized_intervention"] = exploded["normalized_intervention_list"].map(_normalize_name)
    exploded = exploded[exploded["normalized_intervention"].notna()].copy()

    if exploded.empty:
        out_path.write_text("# Senales en ensayos SOP\n\nNo hay intervenciones utilizables tras la normalizacion.\n", encoding="utf-8")
        return out_path

    grouped = (
        exploded.groupby("normalized_intervention", dropna=False)
        .agg(
            studies=("nct_id", "nunique"),
            mean_n=("enrollment", "mean"),
            results_rate=("has_results", "mean"),
            completed_rate=("status", lambda s: s.astype(str).str.contains("COMPLETED", case=False, na=False).mean()),
        )
        .reset_index()
    )

    grouped["mean_n"] = grouped["mean_n"].fillna(0)
    grouped["results_rate"] = grouped["results_rate"].fillna(0)
    grouped["completed_rate"] = grouped["completed_rate"].fillna(0)

    grouped["signal_score"] = (
        np.log1p(grouped["studies"]) * 0.45
        + np.log1p(grouped["mean_n"]) * 0.25
        + grouped["results_rate"] * 0.20
        + grouped["completed_rate"] * 0.10
    )

    top = grouped.sort_values(["signal_score", "studies"], ascending=[False, False]).head(top_n)

    lines = [
        "# Senales en ensayos SOP",
        "",
        "Ranking exploratorio por intervencion normalizada:",
        "",
    ]
    for _, r in top.iterrows():
        lines.append(
            f"- {r['normalized_intervention']}: score={r['signal_score']:.3f}, estudios={int(r['studies'])}, "
            f"n medio={r['mean_n']:.1f}, tasa resultados={r['results_rate']:.2f}, tasa completados={r['completed_rate']:.2f}"
        )

    lines.append("")
    lines.append("Nota: score exploratorio para priorizar lectura critica, no inferencia causal.")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-n", type=int, default=25)
    args = parser.parse_args()

    path = anomaly_scan(top_n=args.top_n)
    print(f"Signals report: {path}")
