"""Nucleo de decisao do servico (Etapa 5).

Reaproveita a politica contextual da Etapa 4 e, alem do braco, produz os **reason
codes** (justificativa) e a resposta auditavel completa. A funcao `decide_with_reasons`
replica a MESMA ordem de decisao de `context_policy.decide_arm` — um teste garante que os
bracos coincidem, evitando divergencia entre as camadas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import pandas as pd

from src.bandits.environment import SYNTH_DIR
from src.data.metadata import PDAYS_NOT_CONTACTED
from src.evaluation.context_policy import (
    VALID_CONTACTS,
    compute_arm_scores,
    compute_selection_probabilities,
    greedy_arm_id,
    load_arm_ids,
)
from src.service.audit import write_audit_record
from src.service.contracts import DecisionRequest, DecisionResponse
from src.service.policy_meta import POLICY_VERSION, catalog_hash
from src.service.reason_codes import ReasonCode


@lru_cache(maxsize=1)
def _arm_names() -> dict[str, str]:
    """Mapa arm_id -> arm_name a partir do catalogo sintetico (Etapa 2)."""
    catalog = pd.read_parquet(SYNTH_DIR / "offer_catalog.parquet")
    return dict(zip(catalog["arm_id"], catalog["arm_name"]))


def decide_with_reasons(context: dict[str, Any]) -> tuple[str, list[str]]:
    """Retorna (arm_id, reason_codes) replicando a ordem de context_policy.decide_arm."""
    contact = str(context.get("contact", "unknown"))
    if contact not in VALID_CONTACTS:
        return "arm_control", [ReasonCode.SAFE_FALLBACK_INVALID_CHANNEL.value]

    if context.get("force_safe_fallback"):
        return "arm_control", [ReasonCode.SAFE_FALLBACK_FORCED.value]

    pdays = float(context.get("pdays", PDAYS_NOT_CONTACTED))
    macro = str(context.get("segment_macro_regime", "neutral"))
    poutcome = str(context.get("poutcome", "unknown"))
    age = float(context.get("age", 40))
    if macro == "stress" and pdays == PDAYS_NOT_CONTACTED and age < 30 and poutcome == "unknown":
        return "arm_control", [ReasonCode.SAFE_FALLBACK_HIGH_RISK.value]

    greedy = greedy_arm_id(context)
    if context.get("financial_incentive_blocked") and greedy == "arm_rate_boost":
        return "arm_retention_plus", [ReasonCode.INCENTIVE_BLOCKED_REDIRECT.value]
    return greedy, [ReasonCode.GREEDY_CONTEXT_MATCH.value]


def make_decision(
    request: DecisionRequest,
    *,
    write_audit: bool = True,
    audit_path=None,
) -> DecisionResponse:
    """Decide o braco para um contexto, monta a resposta e (opcional) grava auditoria."""
    context = request.model_dump()
    arm_id, reasons = decide_with_reasons(context)

    arm_ids = load_arm_ids()
    scores = compute_arm_scores(context)
    probs = compute_selection_probabilities(scores)
    idx = arm_ids.index(arm_id)

    response = DecisionResponse(
        decision_id=uuid.uuid4().hex,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        arm_id=arm_id,
        arm_name=_arm_names().get(arm_id, arm_id),
        reason_codes=reasons,
        context_score=round(float(scores[idx]), 6),
        selection_probabilities={aid: round(float(p), 6) for aid, p in zip(arm_ids, probs)},
        policy_version=POLICY_VERSION,
        catalog_hash=catalog_hash(),
    )

    if write_audit:
        write_audit_record(response.model_dump(), context, path=audit_path)

    return response
