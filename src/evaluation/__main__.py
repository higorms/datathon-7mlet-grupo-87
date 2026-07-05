"""CLI da avaliacao offline (Etapa 4).

Uso:
    poetry run python -m src.evaluation
    poetry run python -m src.evaluation --horizon 5000 --seeds 10
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.evaluation.evaluator import evaluate_bandit_matrix, evaluate_golden_set
from src.evaluation.fairness import compute_fairness
from src.evaluation.golden_set import DEFAULT_GOLDEN_SET_PATH
from src.evaluation.report import (
    FIG_DIR,
    REPORTS_DIR,
    plot_fairness,
    plot_sensitivity,
    render_report,
    write_metrics_json,
)
from src.evaluation.sensitivity import run_sensitivity_study

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Avaliacao offline da Etapa 4.")
    parser.add_argument("--golden-set", type=Path, default=DEFAULT_GOLDEN_SET_PATH)
    parser.add_argument("--horizon", type=int, default=20000)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--sensitivity-horizon", type=int, default=5000,
                        help="Horizonte para estudo de sensibilidade (mais rapido).")
    parser.add_argument("--sensitivity-seeds", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("== Avaliacao do golden set ==")
    from src.evaluation.golden_set import load_golden_cases

    cases = load_golden_cases(args.golden_set)
    golden = evaluate_golden_set(cases)
    logger.info("Golden set: %d casos, pass rate=%.1f%%",
                len(golden.results), golden.pass_rate * 100)

    if golden.failures:
        for f in golden.failures:
            logger.warning("FALHA %s: %s", f.case.case_id, f.failure_reason)

    logger.info("== Matriz de metricas bandit ==")
    bandit_results = evaluate_bandit_matrix(horizon=args.horizon, seeds=args.seeds)

    logger.info("== Sensibilidade ==")
    sensitivity = run_sensitivity_study(
        horizon=args.sensitivity_horizon, seeds=args.sensitivity_seeds,
    )

    logger.info("== Fairness de exposicao ==")
    fairness = compute_fairness()

    plot_sensitivity(sensitivity, FIG_DIR / "offline_sensitivity.png")
    plot_fairness(fairness, FIG_DIR / "offline_fairness_exposure.png")

    report = render_report(
        golden, bandit_results, sensitivity, fairness, args.horizon, args.seeds,
    )
    (args.output_dir / "offline-evaluation.md").write_text(report, encoding="utf-8")
    write_metrics_json(
        golden, bandit_results, sensitivity, fairness,
        args.horizon, args.seeds, args.output_dir / "offline-metrics.json",
    )

    print("\n=== Etapa 4 concluida ===")
    print(f"  Golden set: {golden.pass_rate*100:.1f}% pass ({len(golden.results)} casos)")
    if golden.failures:
        print(f"  ATENCAO: {len(golden.failures)} falha(s) no golden set")
        sys.exit(1)
    print("  Artefatos: reports/offline-evaluation.md, reports/offline-metrics.json")
    print("             reports/figures/offline_sensitivity.png, offline_fairness_exposure.png")


if __name__ == "__main__":
    main()
