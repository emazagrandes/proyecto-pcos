"""
Inspector interactivo del Entity Normalizer.

Uso:
    python scripts/inspect_entities.py <comando> [argumento]

Comandos disponibles:
    list                   -- lista las 57 entidades canonicas
    show <nombre>          -- detalle de una entidad y sus alias
    links <nombre>         -- estudios vinculados a una entidad
    signals                -- ranking de intervention_signals
    unknowns               -- terminos sin resolver (new_entity)
    fuzzy                  -- ejemplos de fuzzy matches
    test <termino>         -- prueba el resolver con un termino
    reset                  -- borra las tablas (para empezar de cero)

Ejemplos:
    python scripts/inspect_entities.py list
    python scripts/inspect_entities.py show metformin
    python scripts/inspect_entities.py links letrozole
    python scripts/inspect_entities.py test "glucophage XR"
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "pcos_research.db"


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB), timeout=60)


def cmd_list() -> None:
    conn = get_conn()
    rows = conn.execute(
        "SELECT canonical_name, entity_type, aliases FROM entity ORDER BY entity_id"
    ).fetchall()
    print(f"{'#':>3}  {'Canonical name':<32}  {'Type':<13}  Aliases")
    print("-" * 70)
    for i, r in enumerate(rows, 1):
        n_alias = len(json.loads(r[2])) if r[2] else 0
        print(f"{i:>3}  {r[0]:<32}  {r[1] or '?':<13}  {n_alias} aliases")
    print(f"\nTotal: {len(rows)} entities")
    conn.close()


def cmd_show(name: str) -> None:
    conn = get_conn()
    r = conn.execute(
        "SELECT entity_id, canonical_name, entity_type, aliases FROM entity WHERE canonical_name=?",
        (name.lower(),),
    ).fetchone()
    if not r:
        print(f"No entity found with canonical_name='{name}'")
        # try fuzzy
        all_names = [
            row[0] for row in conn.execute("SELECT canonical_name FROM entity").fetchall()
        ]
        candidates = [n for n in all_names if name.lower() in n]
        if candidates:
            print(f"\nMaybe you meant: {candidates[:5]}")
        conn.close()
        return
    print(f"Entity ID:      {r[0]}")
    print(f"Canonical name: {r[1]}")
    print(f"Type:           {r[2]}")
    print("Aliases:")
    for a in json.loads(r[3] or "[]"):
        print(f"  - {a}")
    n_links = conn.execute(
        "SELECT COUNT(*) FROM article_entity_links WHERE entity_id=?", (r[0],)
    ).fetchone()[0]
    print(f"\nLinked studies: {n_links}")
    conn.close()


def cmd_links(name: str, limit: int = 25) -> None:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT ael.canonical_id, ael.raw_term, ael.method, ael.confidence
        FROM article_entity_links ael
        JOIN entity e ON ael.entity_id = e.entity_id
        WHERE e.canonical_name = ?
        ORDER BY ael.confidence DESC
        LIMIT ?
        """,
        (name.lower(), limit),
    ).fetchall()
    if not rows:
        print(f"No links for entity '{name}'")
        conn.close()
        return
    print(f"Links to '{name}' (top {limit}):")
    print(f"{'Source ID':<22}  {'Raw term':<40}  {'Method':<16}  Conf")
    print("-" * 90)
    for r in rows:
        sid = (r[0] or "")[:22]
        raw = (r[1] or "")[:40]
        print(f"{sid:<22}  {raw:<40}  {r[2]:<16}  {r[3]:.2f}")
    conn.close()


def cmd_signals() -> None:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT e.canonical_name, s.n_studies, s.n_favorable,
               s.consistency_score, s.weighted_score
        FROM intervention_signals s
        JOIN entity e ON s.entity_id = e.entity_id
        ORDER BY s.n_studies DESC
        LIMIT 30
        """
    ).fetchall()
    print(f"{'Entity':<32}  {'Studies':>7}  {'Fav':>4}  {'Cons':>6}  {'Weight':>7}")
    print("-" * 65)
    for r in rows:
        print(f"{r[0]:<32}  {r[1]:>7}  {r[2]:>4}  {r[3]:>6.2f}  {r[4]:>7.2f}")
    conn.close()


def cmd_unknowns() -> None:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT raw_term, COUNT(*) as n
        FROM article_entity_links
        WHERE method = 'new_entity'
        GROUP BY raw_term
        ORDER BY n DESC
        LIMIT 30
        """
    ).fetchall()
    print("Top 30 unresolved terms (created as new_entity):")
    for r in rows:
        print(f"  {r[1]:>3}x  {r[0]}")
    conn.close()


def cmd_fuzzy() -> None:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ael.raw_term, e.canonical_name, ael.confidence, ael.method
        FROM article_entity_links ael
        JOIN entity e ON ael.entity_id = e.entity_id
        WHERE ael.method LIKE 'fuzzy%'
        ORDER BY ael.confidence DESC
        LIMIT 30
        """
    ).fetchall()
    print("Examples of fuzzy matches:")
    print(f"{'Raw term':<42}  -> {'Entity':<24}  {'Method':<16}  Conf")
    print("-" * 95)
    for r in rows:
        raw = (r[0] or "")[:42]
        ent = (r[1] or "")[:24]
        print(f"{raw:<42}  -> {ent:<24}  {r[3]:<16}  {r[2]:.2f}")
    conn.close()


def cmd_test(term: str) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from entity_normalizer import resolve_by_dictionary  # noqa
    canonical, method, conf = resolve_by_dictionary(term)
    print(f"Term:       {term!r}")
    print(f"Resolved:   {canonical}")
    print(f"Method:     {method}")
    print(f"Confidence: {conf:.2f}")


def cmd_reset() -> None:
    conn = get_conn()
    conn.executescript(
        "DROP TABLE IF EXISTS article_entity_links;"
        "DROP TABLE IF EXISTS intervention_signals;"
        "DROP TABLE IF EXISTS entity;"
    )
    conn.commit()
    conn.close()
    print("Tables dropped. Re-run scripts/entity_normalizer.py to rebuild.")


COMMANDS = {
    "list": cmd_list,
    "show": cmd_show,
    "links": cmd_links,
    "signals": cmd_signals,
    "unknowns": cmd_unknowns,
    "fuzzy": cmd_fuzzy,
    "test": cmd_test,
    "reset": cmd_reset,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        return
    cmd = sys.argv[1]
    fn = COMMANDS[cmd]
    if cmd in {"show", "links", "test"}:
        if len(sys.argv) < 3:
            print(f"Command '{cmd}' requires an argument.")
            print(__doc__)
            return
        fn(sys.argv[2])
    else:
        fn()


if __name__ == "__main__":
    main()
