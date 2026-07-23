"""Etapa 7 - Ciclo de vida MLOps.

Como uma nova politica sai de experimento para producao controlada:

    registry    - registro de politicas com estagios (dev/staging/prod), historico e rollback.
    promotion   - approval gate: criterios automaticos + aprovacao humana antes de promover.
    tracking    - rastreio de experimentos em MLflow (params, metricas, artefatos).
    monitoring  - monitoramento de drift de decisao e de recompensa a partir dos logs.
    __main__    - CLI que demonstra o fluxo experimento -> gate -> aprovacao -> promocao/rollback.
"""
