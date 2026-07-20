"""Pipeline ponta a ponta local (Etapas 1-5).

Reproduz a cadeia da solucao em um comando:
  1. Garante dados processados (Etapa 1)
  2. Confirma camada sintetica (Etapa 2)
  3. Avaliacao offline rapida do golden set (Etapa 4)
  4. Demonstra o servico de decisao com auditoria (Etapa 5)

Uso:
    poetry run python scripts/run_pipeline.py
    poetry run python scripts/run_pipeline.py --full-evaluation   # matriz bandit completa

Depois, para subir a API:
    poetry run uvicorn src.service.app:app --reload
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.bandits.environment import SYNTH_DIR  # noqa: E402
from src.data.build_processed import load_processed  # noqa: E402
from src.evaluation.evaluator import evaluate_golden_set  # noqa: E402
from src.evaluation.golden_set import DEFAULT_GOLDEN_SET_PATH, load_golden_cases  # noqa: E402
from src.service.contracts import DecisionRequest  # noqa: E402
from src.service.decision import make_decision  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("run_pipeline")

DEMOS = [
    (
        "Caso tipico (jovem + celular + sucesso)",
        {"age": 22, "contact": "cellular", "poutcome": "success", "pdays": 180,
         "job": "student", "month": "oct", "segment_macro_regime": "tight"},
    ),
    (
        "Trilho de seguranca (canal invalido)",
        {"age": 40, "contact": "email"},
    ),
    (
        "Incentivo bloqueado (redireciona rate_boost)",
        {"age": 30, "contact": "cellular", "poutcome": "success",
         "financial_incentive_blocked": True},
    ),
]


def _run_full_evaluation() -> None:
    """Executa a CLI completa da Etapa 4 (matriz bandit + sensibilidade + fairness)."""
    cmd = [
        sys.executable, "-m", "src.evaluation",
        "--horizon", "5000",
        "--seeds", "5",
        "--sensitivity-horizon", "2000",
        "--sensitivity-seeds", "3",
    ]
    log.info("      executando: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ponta a ponta local (Etapas 1-5).")
    parser.add_argument(
        "--full-evaluation",
        action="store_true",
        help="Roda avaliacao offline completa (matriz bandit + relatorio). Padrao: so golden set.",
    )
    args = parser.parse_args()

    log.info("[1/4] Garantindo dados processados (Etapa 1)...")
    df = load_processed()
    log.info("      processado: %d linhas x %d colunas", df.shape[0], df.shape[1])

    log.info("[2/4] Conferindo camada sintetica (Etapa 2)...")
    catalog = SYNTH_DIR / "offer_catalog.parquet"
    if not catalog.exists():
        raise FileNotFoundError(
            f"{catalog} ausente. Gere a Etapa 2 (notebooks/02_enriquecimento_sintetico.ipynb)."
        )
    log.info("      catalogo presente: %s", catalog.name)

    log.info("[3/4] Avaliacao offline (Etapa 4)...")
    if args.full_evaluation:
        _run_full_evaluation()
    else:
        cases = load_golden_cases(DEFAULT_GOLDEN_SET_PATH)
        golden = evaluate_golden_set(cases)
        log.info(
            "      golden set: %d casos, pass rate=%.1f%%",
            len(golden.results),
            golden.pass_rate * 100,
        )
        if golden.failures:
            for failure in golden.failures:
                log.warning("      FALHA %s: %s", failure.case.case_id, failure.failure_reason)
            raise SystemExit(1)

    log.info("[4/4] Demonstrando o servico de decisao (Etapa 5)...")
    for title, ctx in DEMOS:
        resp = make_decision(DecisionRequest(**ctx))
        print(f"\n>>> {title}")
        print(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2))

    print("\n=== Pipeline concluido ===")
    print("Auditoria gravada em logs/decisions.jsonl")
    print("Para subir a API:   poetry run uvicorn src.service.app:app --reload")
    print("Contrato interativo: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main()
