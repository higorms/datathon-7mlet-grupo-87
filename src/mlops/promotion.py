"""Approval gate de promocao (Etapa 7).

Uma politica candidata so pode ser promovida se (1) passar nos **criterios automaticos**
de qualidade/risco e (2) receber **aprovacao humana** explicita. Sem os dois, a promocao
e bloqueada — evitando que uma politica regressiva chegue a producao.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GateCriteria:
    """Limiares dos criterios automaticos de promocao."""

    min_golden_pass_rate: float = 1.0        # golden set deve passar 100%
    max_regret: float = 300.0                # regret final da politica candidata
    min_optimal_arm_rate: float = 0.60       # fracao de selecoes do braco otimo
    max_fallback_rate: float = 0.30          # teto de decisoes em fallback seguro


@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class GateResult:
    approved_automatic: bool
    checks: list[GateCheck] = field(default_factory=list)

    @property
    def blocked_reasons(self) -> list[str]:
        return [f"{c.name}: {c.detail}" for c in self.checks if not c.passed]

    def promotion_allowed(self, human_approved: bool) -> bool:
        """Promocao exige gate automatico APROVADO **e** aprovacao humana."""
        return self.approved_automatic and human_approved


def evaluate_gate(metrics: dict[str, Any], criteria: GateCriteria | None = None) -> GateResult:
    """Avalia os criterios automaticos sobre as metricas da politica candidata."""
    c = criteria or GateCriteria()
    checks: list[GateCheck] = []

    pass_rate = float(metrics.get("golden_pass_rate", 0.0))
    checks.append(GateCheck(
        "golden_pass_rate",
        pass_rate >= c.min_golden_pass_rate,
        f"{pass_rate:.3f} (min {c.min_golden_pass_rate})",
    ))

    regret = float(metrics.get("regret", float("inf")))
    checks.append(GateCheck(
        "regret",
        regret <= c.max_regret,
        f"{regret:.1f} (max {c.max_regret})",
    ))

    optimal = float(metrics.get("optimal_arm_rate", 0.0))
    checks.append(GateCheck(
        "optimal_arm_rate",
        optimal >= c.min_optimal_arm_rate,
        f"{optimal:.3f} (min {c.min_optimal_arm_rate})",
    ))

    fallback = float(metrics.get("fallback_rate", 0.0))
    checks.append(GateCheck(
        "fallback_rate",
        fallback <= c.max_fallback_rate,
        f"{fallback:.3f} (max {c.max_fallback_rate})",
    ))

    approved = all(chk.passed for chk in checks)
    return GateResult(approved_automatic=approved, checks=checks)
