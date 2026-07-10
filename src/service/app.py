"""API FastAPI que expoe a decisao de forma controlada e auditavel (Etapa 5).

Endpoints:
    POST /decide               - recebe um contexto e devolve a decisao (grava auditoria).
    GET  /health               - liveness/readiness + versao da politica.
    GET  /audit/{decision_id}  - recupera um registro auditavel.
    GET  /docs                 - contrato OpenAPI/Swagger (automatico).

Subir localmente:
    poetry run uvicorn src.service.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.service.audit import read_audit_record
from src.service.contracts import DecisionRequest, DecisionResponse
from src.service.decision import make_decision
from src.service.policy_meta import POLICY_VERSION, catalog_hash
from src.service.reason_codes import REASON_DESCRIPTIONS

app = FastAPI(
    title="Datathon 7MLET - Servico de Decisao (Etapa 5)",
    description=(
        "Expoe a politica contextual de ofertas de forma controlada e auditavel. "
        "Cada decisao retorna braco, reason codes, versao da politica e decision_id, "
        "e e registrada em um log auditavel."
    ),
    version=POLICY_VERSION,
)


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness/readiness para probes (Etapa 6/Azure)."""
    return {
        "status": "ok",
        "policy_version": POLICY_VERSION,
        "catalog_hash": catalog_hash(),
    }


@app.get("/reason-codes", tags=["ops"])
def reason_codes() -> dict[str, str]:
    """Dicionario de reason codes e suas descricoes."""
    return {str(k): v for k, v in REASON_DESCRIPTIONS.items()}


@app.post("/decide", response_model=DecisionResponse, tags=["decision"])
def decide(request: DecisionRequest) -> DecisionResponse:
    """Recebe um contexto de decisao e devolve o braco escolhido + justificativa."""
    return make_decision(request)


@app.get("/audit/{decision_id}", tags=["decision"])
def audit(decision_id: str) -> dict:
    """Recupera um registro auditavel pelo decision_id."""
    record = read_audit_record(decision_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"decision_id {decision_id!r} nao encontrado.")
    return record
