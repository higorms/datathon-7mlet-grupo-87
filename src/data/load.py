"""Carrega a base bruta e registra a proveniencia (fonte / versao / licenca).

Esta e a "camada de dados em codigo" exigida pela Etapa 1: ponto unico que sabe como
ler a base, de onde ela veio e sob qual licenca, deixando um rastro auditavel.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd

from src.data.download import download_raw
from src.data.metadata import CSV_SEPARATOR, RAW_DIR, RAW_FILENAME, SOURCE

logger = logging.getLogger(__name__)

#: Caminho esperado do CSV bruto local.
SOURCE_RAW_PATH: Path = RAW_DIR / RAW_FILENAME


def file_sha256(path: Path) -> str:
    """SHA-256 do arquivo, usado para fixar a versao exata do dado bruto."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_raw(ensure_download: bool = True) -> tuple[pd.DataFrame, dict]:
    """Carrega o CSV bruto e devolve (DataFrame, proveniencia).

    Args:
        ensure_download: se True, baixa a base caso ainda nao exista localmente.

    Returns:
        df: DataFrame com as colunas originais (inclusive `duration`, ainda sem limpeza).
        provenance: dicionario com fonte, versao, licenca, hash e shape - rastreavel.
    """
    if ensure_download:
        raw_path = download_raw(source="auto")
    else:
        raw_path = SOURCE_RAW_PATH
        if not raw_path.exists():
            raise FileNotFoundError(
                f"{raw_path} nao existe. Rode `python -m src.data.download` primeiro."
            )

    df = pd.read_csv(raw_path, sep=CSV_SEPARATOR)

    provenance = {
        "dataset_name": SOURCE.name,
        "kaggle_slug": SOURCE.kaggle_slug,
        "kaggle_url": SOURCE.kaggle_url,
        "uci_url": SOURCE.uci_url,
        "version": SOURCE.version,
        "license": SOURCE.license,
        "citation": SOURCE.citation,
        "raw_filename": RAW_FILENAME,
        "raw_sha256": file_sha256(raw_path),
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "columns": list(df.columns),
    }

    logger.info(
        "Base carregada: %s linhas x %s colunas | fonte=%s | licenca=%s",
        provenance["n_rows"],
        provenance["n_cols"],
        SOURCE.name,
        SOURCE.license,
    )
    return df, provenance
