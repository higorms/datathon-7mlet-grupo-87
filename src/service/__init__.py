"""Etapa 5 - Servico/API demonstravel.

Expoe a decisao da politica contextual (Etapa 4) de forma controlada e auditavel:

    contracts    - contratos Pydantic de entrada (DecisionRequest) e saida (DecisionResponse).
    reason_codes - codigos de justificativa (por que o braco foi escolhido).
    policy_meta  - versao da politica e hash do catalogo (rastreabilidade).
    decision     - nucleo: valida contexto -> decide braco + reason codes -> resposta.
    audit        - log auditavel append-only (JSONL) e leitura por decision_id.
    app          - FastAPI: POST /decide, GET /health, GET /audit/{decision_id}.
    cli          - decisao one-shot por linha de comando (sem subir servidor).
"""
