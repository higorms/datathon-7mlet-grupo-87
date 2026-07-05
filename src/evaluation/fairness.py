"""Analise de fairness de exposicao entre segmentos sinteticos."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.bandits.environment import SYNTH_DIR
from src.data.metadata import PROCESSED_PARQUET
from src.evaluation.context_policy import decide_arm, load_arm_ids

SEGMENT_COLUMNS = ("segment_age_band", "segment_history", "segment_macro_regime")


@dataclass
class FairnessResult:
    segment_column: str
    exposure_matrix: pd.DataFrame  # segmento x arm_id (fracoes)
    greedy_matrix: pd.DataFrame  # referencia gulosa sem exploracao
    max_min_ratio: float
    optimal_arm_std: float
    segment_counts: pd.Series


def _load_events_sample(max_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    path = SYNTH_DIR / "offer_events.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} ausente.")
    events = pd.read_parquet(path)
    if len(events) > max_rows:
        events = events.sample(n=max_rows, random_state=seed)

    # Enriquece com features do dataset processado para decisao contextual completa.
    if PROCESSED_PARQUET.exists():
        processed = pd.read_parquet(PROCESSED_PARQUET).reset_index(drop=True)
        processed["customer_id"] = processed.index.astype("int64")
        extra = processed[
            ["customer_id", "age", "pdays", "previous", "month", "emp_var_rate", "euribor3m"]
        ]
        events = events.merge(extra, on="customer_id", how="left")

    return events.reset_index(drop=True)


def _exposure_by_segment(events: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """Fracao de cada braco por valor de segmento."""
    ct = pd.crosstab(events[segment_col], events["arm_id"], normalize="index")
    for arm in load_arm_ids():
        if arm not in ct.columns:
            ct[arm] = 0.0
    return ct[list(load_arm_ids())]


def _greedy_exposure(events: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """Distribuicao gulosa contextual por segmento (referencia sem exploracao)."""
    ctx_cols = [
        "age", "contact", "poutcome", "pdays", "previous", "job", "month",
        "segment_macro_regime", "segment_history", "segment_age_band",
    ]
    available = [c for c in ctx_cols if c in events.columns]
    rows = []
    for seg_val, group in events.groupby(segment_col):
        arms = []
        for _, row in group.iterrows():
            ctx = {c: row[c] for c in available}
            arms.append(decide_arm(ctx))
        counts = pd.Series(arms).value_counts(normalize=True)
        row = {arm: float(counts.get(arm, 0.0)) for arm in load_arm_ids()}
        row["_segment"] = seg_val
        rows.append(row)
    df = pd.DataFrame(rows).set_index("_segment")
    return df[list(load_arm_ids())]


def compute_fairness(
    max_rows: int = 5000,
    seed: int = 42,
) -> dict[str, FairnessResult]:
    """Calcula fairness de exposicao para cada coluna de segmento."""
    events = _load_events_sample(max_rows, seed)
    results: dict[str, FairnessResult] = {}

    for col in SEGMENT_COLUMNS:
        if col not in events.columns:
            continue
        observed = _exposure_by_segment(events, col)
        greedy = _greedy_exposure(events, col)

        # Max-min ratio sobre braço otimo (arm_rate_boost) entre segmentos.
        optimal_col = "arm_rate_boost"
        if optimal_col in observed.columns:
            rates = observed[optimal_col].to_numpy()
            rates = rates[rates > 0]
            max_min = float(rates.max() / rates.min()) if rates.size and rates.min() > 0 else float("nan")
            opt_std = float(observed[optimal_col].std())
        else:
            max_min = float("nan")
            opt_std = float("nan")

        results[col] = FairnessResult(
            segment_column=col,
            exposure_matrix=observed,
            greedy_matrix=greedy,
            max_min_ratio=max_min,
            optimal_arm_std=opt_std,
            segment_counts=events[col].value_counts(),
        )

    return results


def fairness_summary_table(fairness: dict[str, FairnessResult]) -> pd.DataFrame:
    """Tabela resumo de metricas de fairness por dimensao de segmento."""
    rows = []
    for col, res in fairness.items():
        rows.append(
            {
                "segmento": col,
                "n_grupos": len(res.exposure_matrix),
                "max_min_ratio_otimo": round(res.max_min_ratio, 3),
                "std_exposicao_otimo": round(res.optimal_arm_std, 4),
            }
        )
    return pd.DataFrame(rows)
