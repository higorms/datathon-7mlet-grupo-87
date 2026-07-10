"""Contratos Pydantic de entrada e saida do servico de decisao (Etapa 5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    """Contexto de decisao recebido pelo servico.

    Campos desconhecidos sao ignorados; tipos/limites invalidos geram HTTP 422.
    """

    age: int = Field(ge=18, le=100, description="Idade do cliente (18-100).")
    contact: str = Field(min_length=1, description="Canal (cellular/telephone; outro -> fallback).")
    poutcome: str = Field(default="unknown", description="Resultado da campanha anterior.")
    pdays: int = Field(default=999, ge=0, description="Dias desde ultimo contato (999 = nunca).")
    previous: int = Field(default=0, ge=0, description="Contatos anteriores.")
    job: str = Field(default="unknown", description="Profissao.")
    month: str = Field(default="may", description="Mes do contato.")
    segment_macro_regime: str = Field(default="neutral", description="stress/neutral/tight.")
    segment_history: str | None = Field(default=None, description="cold_start/warm_history.")
    segment_age_band: str | None = Field(default=None, description="Faixa etaria sintetica.")
    financial_incentive_blocked: bool = Field(
        default=False, description="Se True, bloqueia arm_rate_boost."
    )
    force_safe_fallback: bool = Field(
        default=False, description="Se True, forca arm_control."
    )

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "age": 22,
                "contact": "cellular",
                "poutcome": "success",
                "pdays": 180,
                "previous": 2,
                "job": "student",
                "month": "oct",
                "segment_macro_regime": "tight",
            }
        },
    }


class DecisionResponse(BaseModel):
    """Decisao retornada pelo servico, com justificativa e rastreabilidade."""

    decision_id: str
    timestamp: str
    arm_id: str
    arm_name: str
    reason_codes: list[str]
    context_score: float
    selection_probabilities: dict[str, float]
    policy_version: str
    catalog_hash: str
