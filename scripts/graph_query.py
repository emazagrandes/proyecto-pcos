"""
graph_query.py
===============
Multi-hop graph traversal sobre mechanism_links.

Permite al research_agent responder preguntas como:
  "¿qué mecanismos explican el efecto de silibinin en hiperandrogenismo?"
  "¿qué intervenciones actúan sobre AMPK activation?"
  "¿qué relaciones conectan insulin resistance con metformin en 2 saltos?"

Uso directo:
    python scripts/graph_query.py --start "hyperandrogenism" --hops 2
    python scripts/graph_query.py --start "silibinin" --hops 2 --direction outgoing
    python scripts/graph_query.py --start "insulin resistance" --hops 1 --min-conf 0.7
"""

import sqlite3
import argparse
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path("data/processed/pcos_research.db")


def multihop_query(
    conn: sqlite3.Connection,
    start_name: str,
    hops: int = 2,
    direction: str = "both",   # "outgoing" | "incoming" | "both"
    min_conf: float = 0.4,
) -> list[dict]:
    """
    Recorre el grafo mechanism_links hasta `hops` saltos desde start_name.

    Retorna lista de dicts:
      {hop, from_name, from_type, relation, to_name, to_type, confidence, canonical_id}

    Ejemplo para start="hyperandrogenism", hops=2:
      hop=1: hyperandrogenism <--associated_with-- insulin_resistance
      hop=1: hyperandrogenism <--reduces-- silibinin
      hop=2: insulin_resistance <--improves-- berberine
      hop=2: silibinin --inhibits--> NF-kB
    """
    visited = set()
    frontier = {start_name.lower().strip()}
    results = []

    for hop_num in range(1, hops + 1):
        new_frontier = set()
        for node in frontier:
            # Outgoing: node is source
            if direction in ("outgoing", "both"):
                rows = conn.execute("""
                    SELECT source_name, source_type, relation_type,
                           target_name, target_type, confidence, canonical_id
                    FROM mechanism_links
                    WHERE source_name = ?
                      AND confidence >= ?
                """, (node, min_conf)).fetchall()
                for row in rows:
                    neighbor = row[3]
                    results.append({
                        "hop": hop_num,
                        "from_name": row[0], "from_type": row[1],
                        "relation": row[2],
                        "to_name": row[3], "to_type": row[4],
                        "confidence": row[5], "canonical_id": row[6],
                        "direction_arrow": "-->",
                    })
                    if neighbor not in visited:
                        new_frontier.add(neighbor)

            # Incoming: node is target
            if direction in ("incoming", "both"):
                rows = conn.execute("""
                    SELECT source_name, source_type, relation_type,
                           target_name, target_type, confidence, canonical_id
                    FROM mechanism_links
                    WHERE target_name = ?
                      AND confidence >= ?
                """, (node, min_conf)).fetchall()
                for row in rows:
                    neighbor = row[0]
                    results.append({
                        "hop": hop_num,
                        "from_name": row[0], "from_type": row[1],
                        "relation": row[2],
                        "to_name": row[3], "to_type": row[4],
                        "confidence": row[5], "canonical_id": row[6],
                        "direction_arrow": "<--",
                    })
                    if neighbor not in visited:
                        new_frontier.add(neighbor)

        visited |= frontier
        frontier = new_frontier - visited

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        key = (r["from_name"], r["relation"], r["to_name"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return sorted(unique, key=lambda x: (x["hop"], -x["confidence"]))


def summarize_graph(conn: sqlite3.Connection, start_name: str, hops: int = 2) -> str:
    """
    Genera un resumen legible del subgrafo para pasar al LLM como contexto.
    Usado por el research_agent como herramienta #7.
    """
    results = multihop_query(conn, start_name, hops=hops)
    if not results:
        return f"No mechanistic relations found for '{start_name}'."

    # Collect supporting articles
    canonical_ids = {r["canonical_id"] for r in results if r["canonical_id"]}
    art_map = {}
    if canonical_ids:
        placeholders = ",".join("?" * len(canonical_ids))
        rows = conn.execute(
            f"SELECT canonical_id, title, year FROM articles WHERE canonical_id IN ({placeholders})",
            list(canonical_ids),
        ).fetchall()
        art_map = {r[0]: f"{r[1][:60]}... ({r[2]})" for r in rows}

    lines = [f"## Mechanistic graph for: {start_name}\n"]
    current_hop = None
    for r in results:
        if r["hop"] != current_hop:
            current_hop = r["hop"]
            lines.append(f"\n### Hop {current_hop}")
        art_str = art_map.get(r["canonical_id"], "")
        lines.append(
            f"  {r['from_name']} ({r['from_type']}) "
            f"--{r['relation']}--> "
            f"{r['to_name']} ({r['to_type']})  "
            f"[conf={r['confidence']:.2f}]"
            + (f"\n    Source: {art_str}" if art_str else "")
        )

    return "\n".join(lines)


def interventions_for_target(
    conn: sqlite3.Connection,
    target_name: str,
    max_hops: int = 2,
) -> list[tuple[str, int, float]]:
    """
    Encuentra todas las intervenciones que están conectadas a target_name
    en hasta max_hops saltos.
    Retorna: [(intervention_name, hop_distance, max_confidence)]
    Útil para: "¿qué fármacos actúan sobre insulin resistance?"
    """
    results = multihop_query(conn, target_name, hops=max_hops, direction="both")
    interventions = defaultdict(lambda: (999, 0.0))  # name -> (min_hop, max_conf)
    for r in results:
        for name, ntype in [(r["from_name"], r["from_type"]), (r["to_name"], r["to_type"])]:
            if ntype == "intervention" and name != target_name:
                cur_hop, cur_conf = interventions[name]
                interventions[name] = (
                    min(cur_hop, r["hop"]),
                    max(cur_conf, r["confidence"]),
                )
    return sorted(
        [(name, hop, conf) for name, (hop, conf) in interventions.items()],
        key=lambda x: (x[1], -x[2]),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start",  required=True, help="Start node name")
    parser.add_argument("--hops",   type=int, default=2)
    parser.add_argument("--direction", choices=["both","outgoing","incoming"], default="both")
    parser.add_argument("--min-conf", type=float, default=0.4)
    parser.add_argument("--interventions", action="store_true",
                        help="List interventions connected to start node")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH), timeout=30)

    if args.interventions:
        ivs = interventions_for_target(conn, args.start, max_hops=args.hops)
        print(f"\nInterventions connected to '{args.start}' (up to {args.hops} hops):\n")
        for name, hop, conf in ivs:
            print(f"  hop={hop}  conf={conf:.2f}  {name}")
    else:
        summary = summarize_graph(conn, args.start, hops=args.hops)
        print(summary)

    conn.close()
