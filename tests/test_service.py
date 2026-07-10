"""Testes do servico/API de decisao (Etapa 5)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.evaluation.context_policy import decide_arm
from src.evaluation.golden_set import load_golden_cases
from src.service.app import app
from src.service.decision import decide_with_reasons, make_decision
from src.service.contracts import DecisionRequest


@pytest.fixture(autouse=True)
def _isolated_audit(tmp_path, monkeypatch):
    """Isola o log auditavel em um arquivo temporario por teste."""
    monkeypatch.setenv("AUDIT_LOG_PATH", str(tmp_path / "decisions.jsonl"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Contrato e endpoints
# --------------------------------------------------------------------------- #
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["policy_version"]


def test_decide_typical_case(client):
    payload = {"age": 22, "contact": "cellular", "poutcome": "success",
               "pdays": 180, "job": "student", "month": "oct",
               "segment_macro_regime": "tight"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    # Contrato de saida completo.
    for field in ("decision_id", "timestamp", "arm_id", "arm_name", "reason_codes",
                  "context_score", "selection_probabilities", "policy_version", "catalog_hash"):
        assert field in body
    assert body["arm_id"] == "arm_rate_boost"
    assert body["reason_codes"] == ["GREEDY_CONTEXT_MATCH"]


def test_invalid_channel_triggers_safety_rail(client):
    resp = client.post("/decide", json={"age": 40, "contact": "email"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["arm_id"] == "arm_control"
    assert body["reason_codes"] == ["SAFE_FALLBACK_INVALID_CHANNEL"]


def test_incentive_blocked_redirect(client):
    payload = {"age": 30, "contact": "cellular", "poutcome": "success",
               "financial_incentive_blocked": True}
    resp = client.post("/decide", json=payload)
    body = resp.json()
    assert body["arm_id"] != "arm_rate_boost"
    assert body["arm_id"] == "arm_retention_plus"
    assert body["reason_codes"] == ["INCENTIVE_BLOCKED_REDIRECT"]


def test_high_risk_fallback(client):
    payload = {"age": 24, "contact": "cellular", "poutcome": "unknown",
               "pdays": 999, "segment_macro_regime": "stress"}
    resp = client.post("/decide", json=payload)
    body = resp.json()
    assert body["arm_id"] == "arm_control"
    assert body["reason_codes"] == ["SAFE_FALLBACK_HIGH_RISK"]


def test_invalid_input_returns_422(client):
    # age abaixo do minimo (18) -> erro de validacao.
    resp = client.post("/decide", json={"age": 15, "contact": "cellular"})
    assert resp.status_code == 422
    # contact ausente (obrigatorio) -> erro de validacao.
    resp2 = client.post("/decide", json={"age": 30})
    assert resp2.status_code == 422


# --------------------------------------------------------------------------- #
# Auditoria
# --------------------------------------------------------------------------- #
def test_audit_record_written_and_retrievable(client):
    resp = client.post("/decide", json={"age": 45, "contact": "telephone"})
    decision_id = resp.json()["decision_id"]

    audit = client.get(f"/audit/{decision_id}")
    assert audit.status_code == 200
    record = audit.json()
    assert record["decision_id"] == decision_id
    assert "context" in record
    assert record["policy_version"]
    assert record["reason_codes"]


def test_audit_missing_id_returns_404(client):
    assert client.get("/audit/inexistente").status_code == 404


# --------------------------------------------------------------------------- #
# Consistencia com a politica da Etapa 4
# --------------------------------------------------------------------------- #
def test_decision_matches_context_policy():
    """O braco do servico deve coincidir com decide_arm() para todo o golden set."""
    for case in load_golden_cases():
        arm_service, _ = decide_with_reasons(case.context)
        assert arm_service == decide_arm(case.context), f"divergencia em {case.case_id}"


def test_make_decision_no_audit_flag(tmp_path):
    """write_audit=False nao deve criar o arquivo de auditoria."""
    audit_file = tmp_path / "none.jsonl"
    make_decision(
        DecisionRequest(age=50, contact="cellular"),
        write_audit=False,
        audit_path=audit_file,
    )
    assert not audit_file.exists()
