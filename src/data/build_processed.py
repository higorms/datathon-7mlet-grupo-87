"""Gera o dataset derivado sem vazamento em data/processed/.

Transformacoes aplicadas (todas documentadas no dicionario de dados e no relatorio):
    1. Renomeia colunas com ponto (emp.var.rate -> emp_var_rate, ...).
    2. Remove colunas de vazamento pos-contato (duration) - ver metadata.LEAKAGE_DECISIONS.
    3. Codifica o alvo y ('yes'/'no') no inteiro `subscribed` (1/0) e descarta o y textual.
    4. Remove linhas exatamente duplicadas (reportando a contagem).
    5. Tipa categoricas como 'category' e numericas como tipos compactos.
    6. Persiste em Parquet + um metadata.json com a proveniencia e o resumo do processo.

Uso:
    poetry run python -m src.data.build_processed
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from src.data.load import load_raw
from src.data.metadata import (
    CATEGORICAL_COLUMNS,
    LEAKAGE_COLUMNS_TO_DROP,
    LEAKAGE_DECISIONS,
    NUMERIC_COLUMNS,
    PROCESSED_DIR,
    PROCESSED_METADATA_JSON,
    PROCESSED_PARQUET,
    RAW_TARGET,
    RENAME_MAP,
    TARGET,
)

logger = logging.getLogger(__name__)


def build_processed(write: bool = True) -> tuple[pd.DataFrame, dict]:
    """Constroi o DataFrame processado e (opcionalmente) o persiste.

    Returns:
        df_proc: dataset de decisao, sem vazamento e tipado.
        meta: metadados do processo (proveniencia + resumo das transformacoes).
    """
    df_raw, provenance = load_raw(ensure_download=True)
    n_raw = len(df_raw)

    df = df_raw.rename(columns=RENAME_MAP).copy()

    # 1) Remover colunas de vazamento.
    dropped = [c for c in LEAKAGE_COLUMNS_TO_DROP if c in df.columns]
    df = df.drop(columns=dropped)

    # 2) Codificar o alvo: 'yes'/'no' -> 1/0.
    if RAW_TARGET not in df.columns:
        raise KeyError(f"Coluna alvo '{RAW_TARGET}' ausente nas colunas: {list(df.columns)}")
    mapping = {"yes": 1, "no": 0}
    df[TARGET] = df[RAW_TARGET].str.strip().str.lower().map(mapping).astype("int8")
    if df[TARGET].isna().any():
        raise ValueError("Valores de alvo fora de {'yes','no'} encontrados.")
    df = df.drop(columns=[RAW_TARGET])

    # 3) Remover duplicatas exatas.
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    n_duplicates = n_before - len(df)
    if n_duplicates:
        logger.info("Removidas %d linhas exatamente duplicadas.", n_duplicates)

    # 4) Tipagem: categoricas como category, numericas como tipos compactos.
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("category")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], downcast="integer")

    # Ordena colunas: contexto (features) e, por ultimo, o alvo.
    feature_cols = [c for c in df.columns if c != TARGET]
    df = df[feature_cols + [TARGET]]

    meta = {
        "provenance": provenance,
        "process": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_rows_raw": n_raw,
            "n_rows_processed": int(len(df)),
            "n_duplicates_removed": int(n_duplicates),
            "n_cols_processed": int(df.shape[1]),
            "renamed_columns": RENAME_MAP,
            "leakage_columns_dropped": dropped,
            "leakage_decisions": [
                {"column": d.column, "decision": d.decision, "rationale": d.rationale}
                for d in LEAKAGE_DECISIONS
            ],
            "target_column": TARGET,
            "target_encoding": mapping,
            "feature_columns": feature_cols,
        },
    }

    if write:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(PROCESSED_PARQUET, index=False)
        PROCESSED_METADATA_JSON.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(
            "Processado salvo: %s (%d linhas x %d colunas).",
            PROCESSED_PARQUET,
            len(df),
            df.shape[1],
        )
        logger.info("Metadados salvos: %s", PROCESSED_METADATA_JSON)

    return df, meta


def load_processed() -> pd.DataFrame:
    """Carrega o dataset processado, construindo-o caso ainda nao exista."""
    if not PROCESSED_PARQUET.exists():
        logger.info("Parquet processado ausente; construindo agora.")
        build_processed(write=True)
    return pd.read_parquet(PROCESSED_PARQUET)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    df, meta = build_processed(write=True)
    print(
        f"OK: {meta['process']['n_rows_processed']} linhas, "
        f"{meta['process']['n_cols_processed']} colunas, "
        f"{len(meta['process']['leakage_columns_dropped'])} coluna(s) de vazamento removida(s)."
    )


if __name__ == "__main__":
    main()
