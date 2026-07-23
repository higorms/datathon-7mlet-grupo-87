"""Rastreio de experimentos em MLflow (Etapa 7).

Registra cada avaliacao de politica candidata (params, metricas e tags) num run do
MLflow, dando rastreabilidade do que foi testado antes de promover. Usa backend local
por padrao (`mlruns/`); o tracking_uri e configuravel (ex.: Azure ML na Etapa 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.data.metadata import PROJECT_ROOT

DEFAULT_TRACKING_DIR = PROJECT_ROOT / "mlruns"
EXPERIMENT_NAME = "datathon-policy-lifecycle"


def log_policy_run(
    version: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    tags: dict[str, str] | None = None,
    tracking_uri: str | None = None,
    experiment: str = EXPERIMENT_NAME,
) -> str:
    """Cria um run no MLflow com params/metricas/tags da politica. Retorna o run_id."""
    import mlflow  # import tardio: MLflow so e necessario neste caminho (fora da imagem).

    uri = tracking_uri or DEFAULT_TRACKING_DIR.as_uri()
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment)

    with mlflow.start_run(run_name=version) as run:
        mlflow.set_tag("policy_version", version)
        for key, value in (tags or {}).items():
            mlflow.set_tag(key, value)
        for key, value in params.items():
            mlflow.log_param(key, value)
        for key, value in metrics.items():
            mlflow.log_metric(key, float(value))
        return run.info.run_id


def list_runs(tracking_uri: str | None = None, experiment: str = EXPERIMENT_NAME):
    """Lista os runs do experimento (para inspecao/rastreio)."""
    import mlflow

    uri = tracking_uri or DEFAULT_TRACKING_DIR.as_uri()
    mlflow.set_tracking_uri(uri)
    exp = mlflow.get_experiment_by_name(experiment)
    if exp is None:
        return []
    return mlflow.search_runs(experiment_ids=[exp.experiment_id]).to_dict("records")


def resolve_tracking_dir(tracking_uri: str | None) -> Path:
    """Diretorio local de tracking (para testes/limpeza)."""
    return Path(tracking_uri) if tracking_uri else DEFAULT_TRACKING_DIR
