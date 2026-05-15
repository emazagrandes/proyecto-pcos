import sqlite3
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


TARGET_KEYWORDS = {
    "Metformin": ["metformin"],
    "Inositol": ["inositol", "myo-inositol", "d-chiro-inositol"],
    "Probioticos y microbiota": ["probiotic", "microbiota", "gut microbiota"],
    "Letrozole y reproduccion": ["letrozole", "clomiphene", "ovulation", "fertility"],
    "Acupuntura y sintomas neuropsicologicos": ["acupuncture", "anxiety", "depression"],
}


def _load_table(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception:
        return pd.DataFrame()


def _match_articles(articles: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if articles.empty:
        return articles
    pattern = "|".join(keywords)
    title_text = articles.get("title", pd.Series("", index=articles.index)).fillna("").str.lower()
    summary_text = articles.get("summary_short", pd.Series("", index=articles.index)).fillna("").str.lower()
    return articles.loc[title_text.str.contains(pattern, regex=True) | summary_text.str.contains(pattern, regex=True)].copy()


def _match_trials(trials: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if trials.empty:
        return trials
    pattern = "|".join(keywords)
    intervention_text = trials.get("interventions", pd.Series("", index=trials.index)).fillna("").str.lower()
    title_text = trials.get("title", pd.Series("", index=trials.index)).fillna("").str.lower()
    return trials.loc[intervention_text.str.contains(pattern, regex=True) | title_text.str.contains(pattern, regex=True)].copy()


def _make_hypothesis_block(name: str, articles: pd.DataFrame, trials: pd.DataFrame) -> list[str]:
    article_count = len(articles)
    trial_count = len(trials)
    max_year = None if articles.empty else pd.to_numeric(articles.get("year"), errors="coerce").max()
    max_year_text = f", con actividad reciente hasta {int(max_year)}." if pd.notna(max_year) else "."
    top_titles = articles.get("title", pd.Series(dtype=str)).dropna().head(3).tolist()
    top_interventions = trials.get("interventions", pd.Series(dtype=str)).dropna().head(3).tolist()

    if article_count >= 8:
        evidence_level = "moderado"
    elif article_count >= 3 or trial_count >= 3:
        evidence_level = "emergente"
    else:
        evidence_level = "exploratorio"

    lines = [f"## {name}", ""]
    lines.append(
        f"**Hipotesis mecanistica:** La senal sugiere que {name.lower()} podria modular ejes relevantes de SOP "
        "como ovulacion, resistencia a la insulina, inflamacion o carga sintomatica."
    )
    lines.append("")
    lines.append(
        f"**Plausibilidad clinica:** {article_count} articulos coincidentes y {trial_count} ensayos coincidentes en la base actual"
        + max_year_text
    )
    lines.append("")
    if top_titles:
        lines.append("**Soporte reciente:**")
        for title in top_titles:
            lines.append(f"- {title}")
        lines.append("")
    if top_interventions:
        lines.append("**Senales en ensayos:**")
        for intervention in top_interventions:
            lines.append(f"- {intervention}")
        lines.append("")
    lines.append(
        "**Riesgo/beneficio:** La senal es util para priorizar lectura critica, pero no debe confundirse con recomendacion clinica; "
        "conviene revisar comparadores, sesgo, tamano muestral y desenlaces centrados en paciente."
    )
    lines.append("")
    lines.append(f"**Nivel de evidencia actual:** {evidence_level}.")
    lines.append("")
    return lines


def generate_priority_hypotheses() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "priority_hypotheses.md"
    db_path = PROCESSED_DIR / "pcos_research.db"

    if not db_path.exists():
        out_path.write_text("# Hipotesis prioritarias SOP\n\nNo existe base de datos procesada.\n", encoding="utf-8")
        return out_path

    with sqlite3.connect(db_path) as conn:
        articles = _load_table(conn, "articles")
        trials = _load_table(conn, "trials")

    lines = [
        "# Hipotesis prioritarias SOP",
        "",
        "Documento exploratorio para priorizar lectura critica y seguimiento de senales. No constituye recomendacion clinica.",
        "",
    ]

    for name, keywords in TARGET_KEYWORDS.items():
        matched_articles = _match_articles(articles, keywords).sort_values(
            by=["year", "evidence_tier"], ascending=[False, True]
        ) if not articles.empty else articles
        matched_trials = _match_trials(trials, keywords)
        if matched_articles.empty and matched_trials.empty:
            continue
        lines.extend(_make_hypothesis_block(name, matched_articles, matched_trials))

    if len(lines) <= 4:
        lines.extend(["No se detectaron hipotesis suficientemente trazables con las reglas actuales.", ""])

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = generate_priority_hypotheses()
    print(f"Priority hypotheses report: {path}")
