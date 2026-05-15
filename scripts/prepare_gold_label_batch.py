import argparse
import json
import re
import sqlite3
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


DEFAULT_TOP_K = 100
DEFAULT_RANDOM_SEED = 42
TITLE_BUCKETS = [
    'guideline_like',
    'meta_review_like',
    'observational_like',
    'trial_like',
    'other_like',
]


def _title_bucket(title: str | None) -> str:
    t = (title or '').lower()
    if any(term in t for term in ('meta-analysis', 'systematic review', 'network meta-analysis', 'scoping review', 'umbrella review')):
        return 'meta_review_like'
    if any(term in t for term in ('guideline', 'consensus', 'recommendation', 'practice recommendation', 'delphi')):
        return 'guideline_like'
    if any(term in t for term in ('cohort', 'cross-sectional', 'retrospective', 'prospective', 'survey', 'case-control')):
        return 'observational_like'
    if any(term in t for term in ('trial', 'randomized', 'randomised', 'phase ii', 'phase iii', 'phase iv')):
        return 'trial_like'
    return 'other_like'


def _load_pool(conn: sqlite3.Connection) -> pd.DataFrame:
    query = '''
        SELECT
            a.canonical_id,
            a.title,
            a.year,
            a.journal,
            a.abstract_text,
            a.study_type AS heuristic_study_type,
            a.evidence_tier AS heuristic_evidence_tier,
            a.evidence_score,
            l.study_type_llm,
            l.evidence_tier_llm,
            l.clinical_relevance_llm,
            l.mechanistic_relevance_llm,
            l.utility_score_llm,
            l.llm_label_reasoning,
            l.labeling_status,
            g.review_status,
            g.gold_study_type,
            g.gold_evidence_tier
        FROM articles a
        LEFT JOIN article_llm_labels l ON l.canonical_id = a.canonical_id
        LEFT JOIN article_gold_labels g ON g.canonical_id = a.canonical_id
        WHERE COALESCE(g.review_status, '') = ''
    '''
    return pd.read_sql_query(query, conn)


def _score_row(row: pd.Series) -> float:
    title = str(row.get('title') or '').lower()
    score = 0.0
    if pd.notna(row.get('year')):
        score += min(max(float(row['year']) - 2015, 0), 15)
    score += min(float(row.get('evidence_score') or 0) / 10.0, 10)
    if not row.get('study_type_llm'):
        score += 6
    if any(term in title for term in ('guideline', 'consensus', 'recommendation', 'meta-analysis', 'systematic review', 'cohort', 'trial', 'cross-sectional', 'retrospective', 'prospective', 'survey')):
        score += 4
    if any(term in title for term in ('letter to the editor', 'response to letter', 'commentary', 'editorial')):
        score -= 8
    if any(term in title for term in ('adolescent', 'infertility', 'diagnostic', 'lifestyle', 'cardiometabolic', 'mental', 'amh', 'inositol', 'letrozole', 'metformin')):
        score += 2
    return score


def _build_queue(df: pd.DataFrame, top_k: int, random_seed: int) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out['title_bucket'] = out['title'].map(_title_bucket)
    out['priority_score'] = out.apply(_score_row, axis=1)
    out['review_priority'] = out['priority_score'].map(lambda x: 'high' if x >= 16 else ('medium' if x >= 11 else 'low'))
    out = out.sort_values(['title_bucket', 'priority_score', 'year'], ascending=[True, False, False]).reset_index(drop=True)

    per_bucket = max(1, top_k // len(TITLE_BUCKETS))
    selected_parts = []
    for bucket in TITLE_BUCKETS:
        bucket_df = out[out['title_bucket'] == bucket].head(per_bucket)
        selected_parts.append(bucket_df)
    selected = pd.concat(selected_parts, ignore_index=True)
    if len(selected) < top_k:
        remaining = out[~out['canonical_id'].isin(selected['canonical_id'])].sort_values(['priority_score', 'year'], ascending=[False, False])
        selected = pd.concat([selected, remaining.head(top_k - len(selected))], ignore_index=True)
    selected = selected.drop_duplicates(subset=['canonical_id']).sort_values(['review_priority', 'priority_score', 'year'], ascending=[True, False, False])
    selected['selection_batch'] = f'gold_batch_top_{top_k}_seed_{random_seed}'
    for col in ['gold_study_type','gold_evidence_tier','gold_clinical_relevance','gold_mechanistic_relevance','gold_utility_score','review_notes','reviewer_id']:
        selected[col] = None
    return selected


def _ensure_gold_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS article_gold_labels (
            canonical_id TEXT PRIMARY KEY,
            review_status TEXT NOT NULL,
            gold_study_type TEXT,
            gold_evidence_tier TEXT,
            gold_clinical_relevance TEXT,
            gold_mechanistic_relevance TEXT,
            gold_utility_score REAL,
            review_notes TEXT,
            reviewer_id TEXT,
            source_payload TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )


def _seed_table(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    for row in df.to_dict(orient='records'):
        conn.execute(
            '''
            INSERT INTO article_gold_labels (canonical_id, review_status, source_payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(canonical_id) DO NOTHING
            ''',
            (row['canonical_id'], 'pending_review', json.dumps(row, ensure_ascii=False))
        )


def _write_report(df: pd.DataFrame, csv_path: Path, top_k: int) -> Path:
    path = REPORTS_DIR / 'gold_label_batch_report.md'
    lines = [
        '# Gold Label Batch Report',
        '',
        f'- Articulos en batch: {len(df)}',
        f'- Objetivo solicitado: {top_k}',
        f'- CSV generado: {csv_path}',
        '',
        '## Distribucion por bucket',
        '',
    ]
    counts = df['title_bucket'].value_counts().to_dict() if not df.empty else {}
    for key, value in counts.items():
        lines.append(f'- {key}: {value}')
    lines.extend(['', '## Ejemplos priorizados', ''])
    for _, row in df.head(15).iterrows():
        lines.append(f"### {row['canonical_id']}")
        lines.append(f"- review_priority: {row['review_priority']}")
        lines.append(f"- title_bucket: {row['title_bucket']}")
        lines.append(f"- heuristic: {row['heuristic_study_type']} / {row['heuristic_evidence_tier']}")
        lines.append(f"- llm: {row['study_type_llm']} / {row['evidence_tier_llm']}")
        lines.append(f"- priority_score: {row['priority_score']:.1f}")
        lines.append('')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def prepare_gold_label_batch(top_k: int, random_seed: int) -> tuple[Path, Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROCESSED_DIR / 'pcos_research.db'
    csv_path = PROCESSED_DIR / f'gold_label_batch_{top_k}.csv'
    if not db_path.exists():
        pd.DataFrame().to_csv(csv_path, index=False)
        report_path = _write_report(pd.DataFrame(), csv_path, top_k)
        return csv_path, report_path
    with sqlite3.connect(db_path) as conn:
        _ensure_gold_table(conn)
        pool = _load_pool(conn)
        batch = _build_queue(pool, top_k=top_k, random_seed=random_seed)
        _seed_table(conn, batch)
        conn.commit()
    batch.to_csv(csv_path, index=False, encoding='utf-8')
    report_path = _write_report(batch, csv_path, top_k)
    return csv_path, report_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-k', type=int, default=DEFAULT_TOP_K)
    parser.add_argument('--random-seed', type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args()
    csv_path, report_path = prepare_gold_label_batch(top_k=args.top_k, random_seed=args.random_seed)
    print(f'Gold batch CSV: {csv_path}')
    print(f'Gold batch report: {report_path}')
