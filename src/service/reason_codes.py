"""Reason codes: justificativa auditavel da decisao.

Cada decisao carrega ao menos um codigo explicando POR QUE aquele braco foi escolhido.
Os codigos espelham os trilhos de seguranca e a politica gulosa da Etapa 4.
"""

from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    GREEDY_CONTEXT_MATCH = "GREEDY_CONTEXT_MATCH"
    SAFE_FALLBACK_INVALID_CHANNEL = "SAFE_FALLBACK_INVALID_CHANNEL"
    SAFE_FALLBACK_FORCED = "SAFE_FALLBACK_FORCED"
    SAFE_FALLBACK_HIGH_RISK = "SAFE_FALLBACK_HIGH_RISK"
    INCENTIVE_BLOCKED_REDIRECT = "INCENTIVE_BLOCKED_REDIRECT"


#: Descricao legivel de cada codigo (para docs e auditoria).
REASON_DESCRIPTIONS: dict[str, str] = {
    ReasonCode.GREEDY_CONTEXT_MATCH: "Decisao pela politica gulosa contextual (maior score).",
    ReasonCode.SAFE_FALLBACK_INVALID_CHANNEL: "Canal invalido -> fallback seguro para arm_control.",
    ReasonCode.SAFE_FALLBACK_FORCED: "Fallback seguro forcado por flag -> arm_control.",
    ReasonCode.SAFE_FALLBACK_HIGH_RISK: "Perfil de alto risco (jovem, cold-start, macro stress) -> arm_control.",
    ReasonCode.INCENTIVE_BLOCKED_REDIRECT: "Incentivo financeiro bloqueado -> redireciona de arm_rate_boost para arm_retention_plus.",
}
