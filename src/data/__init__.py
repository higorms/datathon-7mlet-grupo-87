"""Camada de dados (Etapa 1): download, carga, processamento e qualidade da base Kaggle.

Modulos:
    metadata        - fonte/versao/licenca da base e decisao de vazamento centralizada.
    download        - obtem o CSV bruto (kagglehub com fallback para o mirror publico da UCI).
    load            - carrega o CSV bruto e registra a proveniencia (fonte/versao/licenca).
    build_processed - gera o dataset derivado sem vazamento em data/processed/.
    quality         - calcula estatisticas de qualidade reutilizadas no relatorio e na EDA.
    prepare         - orquestrador CLI: download -> processed -> relatorio de qualidade.
"""
