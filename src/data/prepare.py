"""Orquestrador da camada de dados (Etapa 1) - pipeline reproduzivel ponta a ponta.

Executa, em ordem:
    1. download da base bruta (kagglehub -> UCI);
    2. construcao do dataset processado sem vazamento (data/processed/);
    3. geracao do relatorio de qualidade (reports/data-quality.md).

Este e o "comando unico" da Etapa 1:
    poetry run python -m src.data.prepare
"""

from __future__ import annotations

import logging

from src.data.build_processed import build_processed
from src.data.load import load_raw
from src.data.quality import write_quality_report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("prepare")

    log.info("[1/3] Carregando base bruta (download se necessario)...")
    df_raw, _ = load_raw(ensure_download=True)

    log.info("[2/3] Construindo dataset processado (sem vazamento)...")
    df_proc, meta = build_processed(write=True)

    log.info("[3/3] Gerando relatorio de qualidade...")
    stats = write_quality_report(df_raw, df_proc, meta)

    minority = stats["target"].loc[stats["target"]["classe"] == 1, "percentual"].iloc[0]
    print("\n=== Etapa 1 concluida ===")
    print(f"Bruto       : {stats['shape_raw'][0]} x {stats['shape_raw'][1]}")
    print(f"Processado  : {stats['shape_processed'][0]} x {stats['shape_processed'][1]}")
    print(f"Duplicatas  : {stats['n_duplicates_removed']} removidas")
    print(f"Vazamento   : {meta['process']['leakage_columns_dropped']} removida(s)")
    print(f"Conversao   : {minority}% (classe positiva)")
    print(f"corr(duration, alvo) = {stats['leakage']['pointbiserial_corr_duration_target']}")
    print("Artefatos: data/processed/bank_marketing.parquet, data/processed/metadata.json,")
    print("           reports/data-quality.md")


if __name__ == "__main__":
    main()
