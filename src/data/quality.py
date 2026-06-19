"""Calcula estatisticas de qualidade da base e gera reports/data-quality.md.

As mesmas funcoes sao reutilizadas pelo notebook de EDA, de modo que relatorio e
notebook reportem exatamente os mesmos numeros (uma unica fonte da verdade).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.data.metadata import (
    CATEGORICAL_COLUMNS,
    MISSING_CATEGORY_TOKEN,
    NUMERIC_COLUMNS,
    PDAYS_NOT_CONTACTED,
    RAW_TARGET,
    REPORTS_DIR,
    TARGET,
)

logger = logging.getLogger(__name__)


def target_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem e percentual de cada classe do alvo."""
    counts = df[TARGET].value_counts().sort_index()
    pct = (counts / counts.sum() * 100).round(2)
    return pd.DataFrame({"classe": counts.index, "contagem": counts.values, "percentual": pct.values})


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """NaN reais + categoria 'unknown' (ausencia disfarcada) por coluna."""
    rows = []
    for col in df.columns:
        n_nan = int(df[col].isna().sum())
        n_unknown = 0
        if str(df[col].dtype) in ("object", "category"):
            n_unknown = int((df[col].astype("string") == MISSING_CATEGORY_TOKEN).sum())
        total_missing = n_nan + n_unknown
        rows.append(
            {
                "coluna": col,
                "nan": n_nan,
                "unknown": n_unknown,
                "ausentes_total": total_missing,
                "ausentes_%": round(total_missing / len(df) * 100, 2),
            }
        )
    out = pd.DataFrame(rows).sort_values("ausentes_total", ascending=False)
    return out.reset_index(drop=True)


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo estatistico das colunas numericas presentes."""
    cols = [c for c in NUMERIC_COLUMNS if c in df.columns]
    desc = df[cols].describe().T
    desc = desc.rename(
        columns={
            "count": "n",
            "mean": "media",
            "std": "desvio",
            "min": "min",
            "25%": "q25",
            "50%": "mediana",
            "75%": "q75",
            "max": "max",
        }
    )
    return desc.round(3)


def categorical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Cardinalidade e categoria mais frequente por coluna categorica."""
    rows = []
    for col in CATEGORICAL_COLUMNS:
        if col not in df.columns:
            continue
        vc = df[col].value_counts()
        top = vc.index[0]
        rows.append(
            {
                "coluna": col,
                "n_categorias": int(df[col].nunique()),
                "top": str(top),
                "top_freq_%": round(vc.iloc[0] / len(df) * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def leakage_evidence(df_raw: pd.DataFrame) -> dict:
    """Evidencia quantitativa de que `duration` vaza o alvo.

    Calcula a correlacao ponto-bisserial entre duration e o alvo (0/1) e a fracao de
    casos com duration==0 que resultam em 'no' (vazamento determinístico classico).
    """
    y = df_raw[RAW_TARGET].str.strip().str.lower().map({"yes": 1, "no": 0})
    duration = df_raw["duration"].astype(float)
    corr = float(np.corrcoef(duration, y)[0, 1])

    zero_dur = df_raw[duration == 0]
    if len(zero_dur):
        y_zero = zero_dur[RAW_TARGET].str.strip().str.lower()
        share_no_when_zero = float((y_zero == "no").mean())
    else:
        share_no_when_zero = float("nan")

    # Diferenca de media de duration entre quem assinou e quem nao assinou.
    mean_dur_yes = float(duration[y == 1].mean())
    mean_dur_no = float(duration[y == 0].mean())

    return {
        "pointbiserial_corr_duration_target": round(corr, 4),
        "n_duration_zero": int((duration == 0).sum()),
        "share_no_when_duration_zero": round(share_no_when_zero, 4),
        "mean_duration_subscribed": round(mean_dur_yes, 1),
        "mean_duration_not_subscribed": round(mean_dur_no, 1),
    }


def compute_quality(df_raw: pd.DataFrame, df_proc: pd.DataFrame, meta: dict) -> dict:
    """Agrega todas as estatisticas de qualidade num unico dicionario."""
    pdays_never = int((df_proc["pdays"] == PDAYS_NOT_CONTACTED).sum()) if "pdays" in df_proc else 0
    return {
        "shape_raw": (int(df_raw.shape[0]), int(df_raw.shape[1])),
        "shape_processed": (int(df_proc.shape[0]), int(df_proc.shape[1])),
        "n_duplicates_removed": meta["process"]["n_duplicates_removed"],
        "target": target_distribution(df_proc),
        "missing": missing_report(df_proc),
        "numeric": numeric_summary(df_proc),
        "categorical": categorical_summary(df_proc),
        "leakage": leakage_evidence(df_raw),
        "pdays_never_contacted": pdays_never,
        "pdays_never_contacted_pct": round(pdays_never / len(df_proc) * 100, 2),
    }


def _df_to_md(df: pd.DataFrame) -> str:
    """Tabela markdown sem depender de dependencias extras (to_markdown exige tabulate)."""
    headers = list(df.columns)
    lines = ["| " + " | ".join(str(h) for h in headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    return "\n".join(lines)


def render_quality_markdown(stats: dict, meta: dict) -> str:
    """Monta o conteudo do relatorio de qualidade em markdown."""
    prov = meta["provenance"]
    lk = stats["leakage"]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    target_df = stats["target"].copy()
    target_df["classe"] = target_df["classe"].map({0: "0 (nao assinou)", 1: "1 (assinou)"})

    minority_pct = float(stats["target"].loc[stats["target"]["classe"] == 1, "percentual"].iloc[0])

    md = f"""# Relatorio de Qualidade de Dados - Etapa 1

> Gerado automaticamente por `src/data/quality.py` em {generated}.
> Reproduza com: `poetry run python -m src.data.prepare`.

## 1. Proveniencia

| Campo | Valor |
| --- | --- |
| Base | {prov['dataset_name']} |
| Kaggle | {prov['kaggle_url']} |
| Fonte factual (UCI) | {prov['uci_url']} |
| Versao | {prov['version']} |
| Licenca | {prov['license']} |
| Arquivo bruto | `{prov['raw_filename']}` |
| SHA-256 (bruto) | `{prov['raw_sha256']}` |

Citacao: {prov['citation']}

## 2. Dimensoes

| Conjunto | Linhas | Colunas |
| --- | --- | --- |
| Bruto (raw) | {stats['shape_raw'][0]} | {stats['shape_raw'][1]} |
| Processado (sem vazamento) | {stats['shape_processed'][0]} | {stats['shape_processed'][1]} |

- Linhas exatamente duplicadas removidas: **{stats['n_duplicates_removed']}**.
- Colunas removidas por vazamento: **{', '.join(meta['process']['leakage_columns_dropped']) or 'nenhuma'}**.

## 3. Distribuicao do alvo (`{TARGET}`)

{_df_to_md(target_df)}

> **Desbalanceamento de classe:** apenas **{minority_pct}%** dos casos sao conversoes
> (classe positiva). Isso exige metricas alem da acuracia (ex.: AUC-PR, recall, lift) e
> sera relevante para o tratamento de recompensas no bandit.

## 4. Valores ausentes

No CSV original nao ha celulas vazias, mas varias categoricas usam o token
`"{MISSING_CATEGORY_TOKEN}"` como ausencia disfarcada. Tabela por coluna:

{_df_to_md(stats['missing'])}

> Decisao Etapa 1: **nao imputar** ainda. Documentamos a ausencia e mantemos
> `unknown` como categoria propria; a estrategia de imputacao fica para a modelagem.

## 5. Resumo numerico

{_df_to_md(stats['numeric'].reset_index().rename(columns={'index': 'coluna'}))}

- `pdays == {PDAYS_NOT_CONTACTED}` (cliente nunca contatado antes): **{stats['pdays_never_contacted']}**
  linhas ({stats['pdays_never_contacted_pct']}%). E um **sentinela**, nao um valor continuo.

## 6. Resumo categorico

{_df_to_md(stats['categorical'])}

## 7. Evidencia de vazamento - `duration`

Por que `duration` foi **descartada** (decisao da Etapa 1):

| Evidencia | Valor |
| --- | --- |
| Correlacao ponto-bisserial duration x alvo | **{lk['pointbiserial_corr_duration_target']}** |
| Duracao media - assinou | {lk['mean_duration_subscribed']} s |
| Duracao media - nao assinou | {lk['mean_duration_not_subscribed']} s |
| Casos com `duration == 0` | {lk['n_duration_zero']} |
| Fracao 'no' quando `duration == 0` | {lk['share_no_when_duration_zero']} |

> A `duration` so e conhecida **depois** da ligacao - quando o desfecho ja ocorreu.
> A forte correlacao e o padrao `duration==0 => 'no'` confirmam vazamento pos-contato.
> Mante-la inflaria artificialmente qualquer metrica. **Coluna removida do dataset de decisao.**

## 8. Conclusao

- Origem, versao e licenca rastreaveis (secao 1) e fixadas por hash.
- Dataset de decisao **sem vazamento pos-contato** (secao 7).
- Principais riscos para as proximas etapas: **forte desbalanceamento** (secao 3) e
  **ausencia disfarcada de `unknown`** em colunas socioeconomicas (secao 4).
"""
    return md


def write_quality_report(df_raw: pd.DataFrame, df_proc: pd.DataFrame, meta: dict) -> dict:
    """Calcula as estatisticas e grava reports/data-quality.md. Retorna as stats."""
    stats = compute_quality(df_raw, df_proc, meta)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "data-quality.md"
    out.write_text(render_quality_markdown(stats, meta), encoding="utf-8")
    logger.info("Relatorio de qualidade salvo em %s", out)
    return stats
