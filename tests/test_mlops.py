"""Testes do ciclo de vida MLOps (Etapa 7): registro, gate, monitoramento e tracking."""

from __future__ import annotations

import pytest

from src.mlops.monitoring import (
    classify_drift,
    decision_distribution,
    population_stability_index,
    reward_trend,
)
from src.mlops.promotion import GateCriteria, evaluate_gate
from src.mlops.registry import PolicyRegistry
from src.mlops.tracking import log_policy_run

GOOD_METRICS = {"golden_pass_rate": 1.0, "regret": 60.0, "optimal_arm_rate": 0.9, "fallback_rate": 0.2}


# --------------------------------------------------------------------------- #
# Registro e estagios
# --------------------------------------------------------------------------- #
def test_register_and_active():
    reg = PolicyRegistry()
    reg.register("v1", {"m": 1}, stage="prod")
    assert reg.active("prod") == "v1"
    assert reg.get("v1")["stage"] == "prod"


def test_promote_sequential():
    reg = PolicyRegistry()
    reg.register("v2", GOOD_METRICS, stage="dev")
    reg.promote("v2", "staging", actor="t")
    reg.promote("v2", "prod", actor="t")
    assert reg.active("prod") == "v2"
    assert reg.get("v2")["stage"] == "prod"


def test_promote_invalid_transition_raises():
    reg = PolicyRegistry()
    reg.register("v2", GOOD_METRICS, stage="dev")
    with pytest.raises(ValueError):
        reg.promote("v2", "prod", actor="t")  # dev -> prod (pula staging)


def test_rollback_restores_previous_prod():
    reg = PolicyRegistry()
    reg.register("v1", GOOD_METRICS, stage="prod")
    reg.register("v2", GOOD_METRICS, stage="dev")
    reg.promote("v2", "staging", actor="t")
    reg.promote("v2", "prod", actor="t")
    assert reg.active("prod") == "v2"
    restored = reg.rollback("prod", actor="oncall")
    assert restored == "v1"
    assert reg.active("prod") == "v1"
    assert reg.get("v2")["stage"] == "archived"


def test_registry_roundtrip(tmp_path):
    reg = PolicyRegistry(path=tmp_path / "reg.json")
    reg.register("v1", {"m": 1}, stage="prod")
    reg.save()
    reloaded = PolicyRegistry.load(tmp_path / "reg.json")
    assert reloaded.active("prod") == "v1"


# --------------------------------------------------------------------------- #
# Approval gate
# --------------------------------------------------------------------------- #
def test_gate_approves_good_metrics():
    result = evaluate_gate(GOOD_METRICS, GateCriteria())
    assert result.approved_automatic
    assert result.promotion_allowed(human_approved=True)
    assert not result.promotion_allowed(human_approved=False)  # exige humano


def test_gate_blocks_high_regret():
    bad = {**GOOD_METRICS, "regret": 500.0}
    result = evaluate_gate(bad, GateCriteria())
    assert not result.approved_automatic
    assert any("regret" in r for r in result.blocked_reasons)


def test_gate_blocks_low_pass_rate():
    bad = {**GOOD_METRICS, "golden_pass_rate": 0.8}
    assert not evaluate_gate(bad).approved_automatic


# --------------------------------------------------------------------------- #
# Monitoramento
# --------------------------------------------------------------------------- #
def test_decision_distribution():
    records = [
        {"arm_id": "arm_control", "reason_codes": ["SAFE_FALLBACK_INVALID_CHANNEL"]},
        {"arm_id": "arm_rate_boost", "reason_codes": ["GREEDY_CONTEXT_MATCH"]},
    ]
    dist = decision_distribution(records)
    assert dist["n"] == 2
    assert dist["arm"]["arm_control"] == 0.5
    assert dist["fallback_rate"] == 0.5


def test_psi_zero_for_identical():
    d = {"a": 0.5, "b": 0.5}
    assert population_stability_index(d, d) == pytest.approx(0.0, abs=1e-9)
    assert classify_drift(population_stability_index(d, d)).level == "none"


def test_psi_detects_shift():
    ref = {"a": 0.9, "b": 0.1}
    cur = {"a": 0.1, "b": 0.9}
    psi = population_stability_index(ref, cur)
    assert psi > 0.25
    assert classify_drift(psi).drifted


def test_reward_trend_shape():
    trend = reward_trend(n_bins=5)
    assert len(trend) == 5
    assert {"reward_rate", "n"}.issubset(trend.columns)


# --------------------------------------------------------------------------- #
# Tracking (MLflow)
# --------------------------------------------------------------------------- #
def test_mlflow_logs_run(tmp_path):
    uri = (tmp_path / "mlruns").as_uri()
    run_id = log_policy_run(
        version="test-policy",
        params={"horizon": 100},
        metrics={"regret": 10.0},
        tracking_uri=uri,
    )
    assert isinstance(run_id, str) and len(run_id) > 0
