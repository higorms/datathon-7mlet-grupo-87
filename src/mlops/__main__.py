"""CLI do ciclo de vida MLOps (Etapa 7).

Demonstra como uma politica candidata sai de experimento para producao controlada:

    experimento -> rastreio (MLflow) -> approval gate -> aprovacao humana -> promocao
    (dev -> staging -> prod) -> rollback documentado.

Uso:
    poetry run python -m src.mlops --candidate context-greedy-v2-rc --approve
    poetry run python -m src.mlops --candidate context-greedy-v2-rc --approve --demo-rollback
    poetry run python -m src.mlops --no-mlflow            # pula o rastreio MLflow
"""

from __future__ import annotations

import argparse
import logging

from src.bandits.environment import build_environment_from_catalog
from src.bandits.policies import ThompsonSampling
from src.bandits.simulation import run_policy
from src.evaluation.evaluator import evaluate_golden_set
from src.evaluation.golden_set import load_golden_cases
from src.mlops.promotion import GateCriteria, evaluate_gate
from src.mlops.registry import PolicyRegistry
from src.mlops.tracking import log_policy_run
from src.service.decision import decide_with_reasons

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mlops")


def evaluate_candidate(horizon: int = 5000, seeds: int = 8) -> dict[str, float]:
    """Calcula as metricas de qualidade/risco da politica candidata."""
    # Qualidade contextual: golden set.
    golden = evaluate_golden_set()
    pass_rate = golden.pass_rate

    # Risco de fallback: fracao de decisoes em trilho de seguranca no golden set.
    cases = load_golden_cases()
    fallbacks = sum(
        1 for c in cases if decide_with_reasons(c.context)[1][0].startswith("SAFE_FALLBACK")
    )
    fallback_rate = fallbacks / len(cases)

    # Desempenho adaptativo (proxy): Thompson Sampling no ambiente do catalogo.
    env = build_environment_from_catalog()
    ts = run_policy(lambda: ThompsonSampling(), env, horizon, seeds)

    return {
        "golden_pass_rate": round(pass_rate, 4),
        "fallback_rate": round(fallback_rate, 4),
        "regret": round(ts.final_regret_mean, 2),
        "optimal_arm_rate": round(ts.optimal_arm_rate, 4),
        "conversion_rate": round(ts.conversion_rate, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ciclo de vida MLOps (Etapa 7).")
    parser.add_argument("--candidate", default="context-greedy-v2-rc",
                        help="Identificador da politica candidata.")
    parser.add_argument("--approve", action="store_true",
                        help="Aprovacao HUMANA da promocao (sem isso, gate nao promove).")
    parser.add_argument("--demo-rollback", action="store_true",
                        help="Demonstra rollback do prod apos a promocao.")
    parser.add_argument("--no-mlflow", action="store_true", help="Pula o rastreio MLflow.")
    parser.add_argument("--persist", action="store_true",
                        help="Grava o registro no arquivo versionado (padrao: registro em memoria).")
    args = parser.parse_args()

    log.info("[1/5] Avaliando politica candidata '%s'...", args.candidate)
    metrics = evaluate_candidate()
    for k, v in metrics.items():
        log.info("      %-18s = %s", k, v)

    log.info("[2/5] Rastreando experimento...")
    if args.no_mlflow:
        log.info("      (MLflow pulado por --no-mlflow)")
    else:
        run_id = log_policy_run(
            version=args.candidate,
            params={"horizon": 5000, "seeds": 8, "policy_type": "context-greedy"},
            metrics=metrics,
            tags={"stage": "candidate", "gate": "pending"},
        )
        log.info("      MLflow run_id=%s (experimento datathon-policy-lifecycle)", run_id)

    log.info("[3/5] Approval gate (criterios automaticos)...")
    gate = evaluate_gate(metrics, GateCriteria())
    for c in gate.checks:
        log.info("      [%s] %s: %s", "PASS" if c.passed else "FAIL", c.name, c.detail)
    log.info("      gate automatico: %s", "APROVADO" if gate.approved_automatic else "BLOQUEADO")

    log.info("[4/5] Decisao de promocao (gate + aprovacao humana)...")
    human = args.approve
    log.info("      aprovacao humana: %s", "SIM (--approve)" if human else "NAO")
    allowed = gate.promotion_allowed(human)
    if not allowed:
        log.warning("      PROMOCAO BLOQUEADA. Motivos: %s",
                    gate.blocked_reasons or ["falta aprovacao humana"])
        raise SystemExit(0 if gate.approved_automatic else 1)

    # Registro seedado com a politica atual em prod.
    registry = PolicyRegistry.load()
    if not registry.active("prod"):
        registry.register("context-greedy-v1", {"golden_pass_rate": 1.0},
                          description="Politica servida atual", stage="prod", actor="seed")
    prev_prod = registry.active("prod")

    log.info("[5/5] Promovendo '%s' dev -> staging -> prod...", args.candidate)
    registry.register(args.candidate, metrics, description="Release candidate", stage="dev",
                      actor="mlops-cli")
    registry.promote(args.candidate, "staging", actor="mlops-cli", note="gate ok")
    registry.promote(args.candidate, "prod", actor="human-approver", note="aprovacao humana")
    log.info("      PROD agora = %s (anterior: %s)", registry.active("prod"), prev_prod)

    if args.demo_rollback:
        restored = registry.rollback("prod", actor="oncall", note="degradacao detectada")
        log.info("      ROLLBACK -> PROD restaurado para: %s", restored)

    if args.persist:
        path = registry.save()
        log.info("      registro salvo em %s", path)

    print("\n=== Ciclo MLOps concluido ===")
    print(f"Candidato   : {args.candidate}")
    print(f"Gate auto   : {'APROVADO' if gate.approved_automatic else 'BLOQUEADO'}")
    print(f"Prod atual  : {registry.active('prod')}")
    print("Registro de politicas: mlops/policy_registry.json (use --persist para gravar)")


if __name__ == "__main__":
    main()
