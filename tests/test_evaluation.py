"""Testes da avaliacao offline e golden set (Etapa 4)."""

from __future__ import annotations

import json

from src.evaluation.context_policy import compute_arm_scores, decide_arm, greedy_arm_id
from src.evaluation.evaluator import evaluate_golden_set
from src.evaluation.fairness import compute_fairness
from src.evaluation.golden_set import DEFAULT_GOLDEN_SET_PATH, coverage_summary, load_golden_cases
from src.evaluation.schema import GoldenCase


def test_golden_set_tem_minimo_20_casos():
    cases = load_golden_cases()
    assert len(cases) >= 20


def test_golden_set_cobertura_por_categoria():
    cases = load_golden_cases()
    coverage = coverage_summary(cases)
    for cat in ("typical", "edge", "segment", "adversarial"):
        assert coverage.get(cat, 0) >= 4, f"Categoria {cat} com menos de 4 casos"


def test_golden_set_valida_pydantic():
    cases = load_golden_cases()
    assert all(isinstance(c, GoldenCase) for c in cases)


def test_greedy_arm_caso_tipico_rate_boost():
    ctx = {
        "age": 22,
        "contact": "cellular",
        "poutcome": "success",
        "pdays": 180,
        "previous": 2,
        "month": "oct",
        "segment_macro_regime": "tight",
    }
    assert greedy_arm_id(ctx) == "arm_rate_boost"


def test_decide_arm_fallback_canal_invalido():
    ctx = {"age": 25, "contact": "email", "pdays": 999, "segment_macro_regime": "neutral"}
    assert decide_arm(ctx) == "arm_control"


def test_decide_arm_incentivo_bloqueado():
    ctx = {
        "age": 35,
        "contact": "cellular",
        "poutcome": "success",
        "pdays": 180,
        "previous": 2,
        "month": "oct",
        "segment_macro_regime": "tight",
        "financial_incentive_blocked": True,
    }
    assert decide_arm(ctx) == "arm_retention_plus"


def test_scores_tem_cinco_bracos():
    scores = compute_arm_scores({"age": 40, "contact": "cellular", "pdays": 999})
    assert scores.shape == (5,)


def test_avaliador_pass_rate_100_no_golden_set_versionado():
    result = evaluate_golden_set()
    assert result.pass_rate == 1.0, [
        (f.case.case_id, f.failure_reason) for f in result.failures
    ]


def test_fairness_retorna_segmentos():
    fairness = compute_fairness(max_rows=500, seed=0)
    assert "segment_macro_regime" in fairness
    assert len(fairness["segment_macro_regime"].exposure_matrix) >= 2


def test_golden_set_jsonl_bem_formado():
    assert DEFAULT_GOLDEN_SET_PATH.exists()
    with DEFAULT_GOLDEN_SET_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                json.loads(line)
