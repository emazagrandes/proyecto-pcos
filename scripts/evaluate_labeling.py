import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


DEFAULT_ONLY_STATUSES = ["codex_high_confidence", "proposed_by_codex"]


def _load_eval_frame(conn: sqlite3.Connection, statuses: list[str]) -> pd.DataFrame:
    placeholders = ",".join("?" for _ in statuses)
    query = f"""
        SELECT
            g.canonical_id,
            a.title,
            g.review_status,
            g.gold_study_type,
            g.gold_evidence_tier,
            g.gold_clinical_relevance,
            g.gold_mechanistic_relevance,
            g.gold_utility_score,
            a.study_type AS heuristic_study_type,
            a.evidence_tier AS heuristic_evidence_tier,
            a.evidence_score AS heuristic_evidence_score,
            l.study_type_llm,
            l.evidence_tier_llm,
            l.clinical_relevance_llm,
            l.mechanistic_relevance_llm,
            l.utility_score_llm,
            l.prompt_version,
            l.labeling_status
        FROM article_gold_labels g
        JOIN articles a ON a.canonical_id = g.canonical_id
        LEFT JOIN article_llm_labels l ON l.canonical_id = g.canonical_id
        WHERE g.review_status IN ({placeholders})
          AND g.gold_study_type IS NOT NULL
          AND g.gold_evidence_tier IS NOT NULL
        ORDER BY g.gold_utility_score DESC, a.year DESC
    """
    return pd.read_sql_query(query, conn, params=statuses)


def _match_rate(df: pd.DataFrame, pred_col: str, gold_col: str) -> float | None:
    subset = df[[pred_col, gold_col]].dropna()
    if subset.empty:
        return None
    return float((subset[pred_col] == subset[gold_col]).mean())


def _build_summary(df: pd.DataFrame) -> dict:
    return {
        "n": len(df),
        "heuristic_study_type_acc": _match_rate(df, "heuristic_study_type", "gold_study_type"),
        "llm_study_type_acc": _match_rate(df, "study_type_llm", "gold_study_type"),
        "heuristic_tier_acc": _match_rate(df, "heuristic_evidence_tier", "gold_evidence_tier"),
        "llm_tier_acc": _match_rate(df, "evidence_tier_llm", "gold_evidence_tier"),
        "llm_clinical_cov": None if df.empty else float(df["clinical_relevance_llm"].notna().mean()),
        "llm_utility_cov": None if df.empty else float(df["utility_score_llm"].notna().mean()),
    }


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def evaluate_labels(statuses: list[str]) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROCESSED_DIR / "pcos_research.db"
    csv_path = PROCESSED_DIR / "label_evaluation.csv"
    report_path = REPORTS_DIR / "label_evaluation.md"

    if not db_path.exists():
        pd.DataFrame().to_csv(csv_path, index=False)
        report_path.write_text("# Label Evaluation\n\nNo database found.\n", encoding="utf-8")
        return csv_path, report_path

    with sqlite3.connect(db_path) as conn:
        df = _load_eval_frame(conn, statuses)

    df["heuristic_study_match"] = df["heuristic_study_type"] == df["gold_study_type"]
    df["llm_study_match"] = df["study_type_llm"] == df["gold_study_type"]
    df["heuristic_tier_match"] = df["heuristic_evidence_tier"] == df["gold_evidence_tier"]
    df["llm_tier_match"] = df["evidence_tier_llm"] == df["gold_evidence_tier"]
    df["winner_study_type"] = df.apply(
        lambda row: "tie"
        if row["heuristic_study_match"] == row["llm_study_match"]
        else ("llm" if row["llm_study_match"] else "heuristic"),
        axis=1,
    )
    df["winner_tier"] = df.apply(
        lambda row: "tie"
        if row["heuristic_tier_match"] == row["llm_tier_match"]
        else ("llm" if row["llm_tier_match"] else "heuristic"),
        axis=1,
    )

    df.to_csv(csv_path, index=False, encoding="utf-8")
    summary = _build_summary(df)
    study_winners = df["winner_study_type"].value_counts().to_dict() if not df.empty else {}
    tier_winners = df["winner_tier"].value_counts().to_dict() if not df.empty else {}

    lines = [
        "# Label Evaluation",
        "",
        f"- Articulos evaluados: {summary['n']}",
        f"- Heuristica study_type vs gold: {_fmt_pct(summary['heuristic_study_type_acc'])}",
        f"- LLM study_type vs gold: {_fmt_pct(summary['llm_study_type_acc'])}",
        f"- Heuristica evidence_tier vs gold: {_fmt_pct(summary['heuristic_tier_acc'])}",
        f"- LLM evidence_tier vs gold: {_fmt_pct(summary['llm_tier_acc'])}",
        f"- Cobertura LLM clinical_relevance: {_fmt_pct(summary['llm_clinical_cov'])}",
        f"- Cobertura LLM utility_score: {_fmt_pct(summary['llm_utility_cov'])}",
        "",
        "## Ganadores por campo",
        "",
        f"- study_type: {study_winners}",
        f"- evidence_tier: {tier_winners}",
        "",
        "## Ejemplos",
        "",
    ]

    for _, row in df.head(10).iterrows():
        lines.append(f"### {row['canonical_id']}")
        lines.append(f"- gold: {row['gold_study_type']} / {row['gold_evidence_tier']}")
        lines.append(f"- heuristica: {row['heuristic_study_type']} / {row['heuristic_evidence_tier']}")
        lines.append(f"- llm: {row['study_type_llm']} / {row['evidence_tier_llm']}")
        lines.append(f"- winner_study_type: {row['winner_study_type']}")
        lines.append(f"- winner_tier: {row['winner_tier']}")
        lines.append(f"- review_status: {row['review_status']}")
        lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--statuses", nargs="*", default=DEFAULT_ONLY_STATUSES)
    args = parser.parse_args()

    csv_path, report_path = evaluate_labels(args.statuses)
    print(f"Evaluation CSV: {csv_path}")
    print(f"Evaluation report: {report_path}")
