"""Avaliacao offline: golden set, matriz de bandits e metricas agregadas."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.bandits.environment import BanditEnvironment, build_environment_from_catalog
from src.bandits.experiment import run_comparison
from src.bandits.simulation import PolicyResult
from src.evaluation.context_policy import compute_arm_scores, decide_arm, load_arm_ids
from src.evaluation.golden_set import load_golden_cases
from src.evaluation.schema import GoldenCase, PassCriteria


@dataclass
class CaseResult:
    case: GoldenCase
    predicted_arm_id: str
    context_score: float
    passed: bool
    failure_reason: str | None = None


@dataclass
class GoldenSetResult:
    results: list[CaseResult]
    pass_rate: float
    pass_rate_by_category: dict[str, float]
    failures: list[CaseResult] = field(default_factory=list)


def _evaluate_pass_criteria(
    criteria: PassCriteria,
    predicted_arm_id: str,
    context_score: float,
) -> tuple[bool, str | None]:
    if criteria.type == "arm_equals":
        if predicted_arm_id != criteria.value:
            return False, f"esperado {criteria.value!r}, obtido {predicted_arm_id!r}"
        return True, None

    if criteria.type == "arm_in_set":
        allowed = set(criteria.value)  # type: ignore[arg-type]
        if predicted_arm_id not in allowed:
            return False, f"esperado em {sorted(allowed)}, obtido {predicted_arm_id!r}"
        return True, None

    if criteria.type == "arm_not_equals":
        if predicted_arm_id == criteria.value:
            return False, f"nao deveria ser {criteria.value!r}"
        return True, None

    if criteria.type == "min_context_score":
        threshold = float(criteria.value)  # type: ignore[arg-type]
        if context_score < threshold:
            return False, f"score {context_score:.3f} < {threshold:.3f}"
        return True, None

    return False, f"criterio desconhecido: {criteria.type}"


def evaluate_golden_set(cases: list[GoldenCase] | None = None) -> GoldenSetResult:
    """Avalia cada caso do golden set contra decide_arm()."""
    cases = cases or load_golden_cases()
    results: list[CaseResult] = []

    for case in cases:
        predicted = decide_arm(case.context)
        scores = compute_arm_scores(case.context)
        arm_ids = load_arm_ids()
        idx = arm_ids.index(predicted)
        score = float(scores[idx])
        passed, reason = _evaluate_pass_criteria(case.pass_criteria, predicted, score)
        results.append(
            CaseResult(
                case=case,
                predicted_arm_id=predicted,
                context_score=score,
                passed=passed,
                failure_reason=reason,
            )
        )

    n_pass = sum(r.passed for r in results)
    pass_rate = n_pass / len(results) if results else 0.0

    by_cat: dict[str, list[bool]] = {}
    for r in results:
        by_cat.setdefault(r.case.category, []).append(r.passed)
    pass_rate_by_category = {
        cat: sum(vals) / len(vals) for cat, vals in sorted(by_cat.items())
    }

    failures = [r for r in results if not r.passed]
    return GoldenSetResult(
        results=results,
        pass_rate=pass_rate,
        pass_rate_by_category=pass_rate_by_category,
        failures=failures,
    )


def evaluate_bandit_matrix(
    env: BanditEnvironment | None = None,
    horizon: int = 20000,
    seeds: int = 30,
    mean_delay: float = 0.0,
) -> list[PolicyResult]:
    """Reexecuta comparacao baseline x bandit (Etapa 3) para a matriz de metricas."""
    env = env or build_environment_from_catalog()
    return run_comparison(env, horizon, seeds, mean_delay=mean_delay)


def arm_id_to_true_p(env: BanditEnvironment) -> dict[str, float]:
    """Mapa arm_id -> taxa Bernoulli do ambiente."""
    return {aid: float(env.true_p[i]) for i, aid in enumerate(env.arm_ids)}
