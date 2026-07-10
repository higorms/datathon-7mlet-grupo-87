"""Contratos Pydantic do golden set (Etapa 4)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExpectedReward(BaseModel):
    """Faixa esperada de recompensa e referencia de true_p do ambiente."""

    min: float = Field(ge=0.0, le=1.0)
    max: float = Field(ge=0.0, le=1.0)
    true_p_ref: float = Field(ge=0.0, le=1.0, description="Taxa Bernoulli do braco no ambiente Etapa 3")


class PassCriteria(BaseModel):
    """Criterio explicito de pass/fail por caso."""

    type: Literal["arm_equals", "arm_in_set", "arm_not_equals", "min_context_score"]
    value: str | list[str] | float


class GoldenCase(BaseModel):
    """Um caso versionado do golden set."""

    case_id: str
    category: Literal["typical", "edge", "segment", "adversarial"]
    title: str
    context: dict[str, Any]
    expected_arm_id: str
    expected_reward: ExpectedReward
    justification: str
    pass_criteria: PassCriteria
    tags: list[str] = Field(default_factory=list)
