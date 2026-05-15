import argparse
import subprocess
import sys


def run_step(cmd: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"Ejecutando: {' '.join(cmd)}")
    print('='*60)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=60)
    parser.add_argument("--retmax", type=int, default=0)
    parser.add_argument("--pubmed-batch-size", type=int, default=200)
    parser.add_argument("--openalex-per-page", type=int, default=100)
    parser.add_argument("--openalex-max-records", type=int, default=0)
    args = parser.parse_args()

    # 1. Descarga de fuentes
    run_step([
        sys.executable, "scripts/fetch_pubmed.py",
        "--days-back", str(args.days_back),
        "--retmax", str(args.retmax),
        "--batch-size", str(args.pubmed_batch_size),
    ])
    run_step([
        sys.executable, "scripts/fetch_openalex.py",
        "--per-page", str(args.openalex_per_page),
        "--max-records", str(args.openalex_max_records),
    ])
    run_step([
        sys.executable, "scripts/fetch_clinicaltrials.py",
        "--query", "polycystic ovary syndrome",
        "--page-size", "100",
    ])

    # 2. Construcción de la base de conocimiento
    run_step([sys.executable, "scripts/build_knowledge_base.py"])

    # 3. Análisis de señales en ensayos
    run_step([sys.executable, "scripts/anomaly_scan.py", "--top-n", "25"])

    # 4. Hipótesis prioritarias
    run_step([sys.executable, "scripts/generate_priority_hypotheses.py"])


if __name__ == "__main__":
    main()
