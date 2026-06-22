"""Testes de validacao da camada de dados (Etapa 1).

Garantem o criterio de aceite: dataset de decisao rastreavel e SEM vazamento
pos-contato. Usam o parquet ja versionado (nao exigem rede).
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.data.build_processed import load_processed
from src.data.metadata import (
    LEAKAGE_COLUMNS_TO_DROP,
    PROCESSED_METADATA_JSON,
    RAW_TARGET,
    TARGET,
)


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return load_processed()


def test_sem_colunas_de_vazamento(df: pd.DataFrame) -> None:
    """Nenhuma coluna marcada como vazamento pode estar no dataset de decisao."""
    for col in LEAKAGE_COLUMNS_TO_DROP:
        assert col not in df.columns, f"Coluna de vazamento '{col}' presente no processado."
    assert "duration" not in df.columns


def test_alvo_binario_e_renomeado(df: pd.DataFrame) -> None:
    """O alvo deve ser 'subscribed' com valores em {0, 1}; o 'y' textual nao deve sobrar."""
    assert TARGET in df.columns
    assert RAW_TARGET not in df.columns
    assert set(df[TARGET].unique()).issubset({0, 1})


def test_sem_nulos(df: pd.DataFrame) -> None:
    """A base original nao tem celulas vazias; o processado deve preservar isso."""
    assert int(df.isna().sum().sum()) == 0


def test_dimensoes_plausiveis(df: pd.DataFrame) -> None:
    """Linhas na ordem esperada (~39k apos remover duplicatas) e 20 colunas."""
    assert 35_000 <= len(df) <= 42_000
    assert df.shape[1] == 20


def test_metadata_proveniencia_completa() -> None:
    """metadata.json deve registrar fonte, versao, licenca e hash do bruto."""
    assert PROCESSED_METADATA_JSON.exists(), "Rode `python -m src.data.prepare` antes."
    meta = json.loads(PROCESSED_METADATA_JSON.read_text(encoding="utf-8"))
    prov = meta["provenance"]
    for campo in ("dataset_name", "version", "license", "kaggle_url", "raw_sha256"):
        assert prov.get(campo), f"Campo de proveniencia ausente: {campo}"
    assert "duration" in meta["process"]["leakage_columns_dropped"]
