"""
create_mechanism_links_table.py
================================
Crea la tabla mechanism_links en pcos_research.db.
Diseñada para almacenar relaciones tipadas del knowledge graph:

    intervention --INHIBITS--> mechanism
    mechanism    --REDUCES-->  biomarker
    biomarker    --INDICATES-> comorbidity
    etc.

Run:
    python scripts/create_mechanism_links_table.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/processed/pcos_research.db")

DDL = """
CREATE TABLE IF NOT EXISTS mechanism_links (
    link_id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Nodo origen
    source_type      TEXT NOT NULL,
    source_id        INTEGER,          -- entity_id si existe en tabla entity
    source_name      TEXT NOT NULL,

    -- Relación tipada
    relation_type    TEXT NOT NULL
                     CHECK(relation_type IN (
                         'activates','inhibits','improves','reduces',
                         'indicates','associated_with','measures','tested_in'
                     )),

    -- Nodo destino
    target_type      TEXT NOT NULL
                     CHECK(target_type IN (
                         'intervention','mechanism','biomarker','outcome',
                         'comorbidity','phenotype','diagnostic_test'
                     )),
    target_id        INTEGER,
    target_name      TEXT NOT NULL,

    -- Evidencia (canonical_id = DOI/PMID, FK a articles.canonical_id)
    canonical_id     TEXT REFERENCES articles(canonical_id),
    confidence       REAL DEFAULT 0.5 CHECK(confidence BETWEEN 0.0 AND 1.0),
    extraction_method TEXT DEFAULT 'llm'
                     CHECK(extraction_method IN ('llm','manual','rule')),
    direction        TEXT DEFAULT 'positive'
                     CHECK(direction IN ('positive','negative','neutral','unclear')),
    raw_snippet      TEXT,    -- fragmento del abstract que respalda esta relación

    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mechlinks_source
    ON mechanism_links(source_name, relation_type);

CREATE INDEX IF NOT EXISTS idx_mechlinks_target
    ON mechanism_links(target_name);

CREATE INDEX IF NOT EXISTS idx_mechlinks_article
    ON mechanism_links(canonical_id);

CREATE INDEX IF NOT EXISTS idx_mechlinks_pair
    ON mechanism_links(source_name, target_name);
"""


def create_table():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    # executescript doesn't honor timeout; split into individual statements
    for stmt in [s.strip() for s in DDL.split(";") if s.strip()]:
        conn.execute(stmt)
    conn.commit()

    # Verify
    cols = conn.execute("PRAGMA table_info(mechanism_links)").fetchall()
    idx  = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='mechanism_links'"
    ).fetchall()
    n    = conn.execute("SELECT COUNT(*) FROM mechanism_links").fetchone()[0]
    conn.close()

    print("mechanism_links created:")
    print(f"  Columns : {[c[1] for c in cols]}")
    print(f"  Indexes : {[i[0] for i in idx]}")
    print(f"  Rows    : {n}")


if __name__ == "__main__":
    create_table()
