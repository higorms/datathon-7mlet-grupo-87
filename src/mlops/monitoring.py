"""Monitoramento de drift de decisao e de recompensa (Etapa 7).

- **Drift de decisao:** compara a distribuicao de bracos/fallbacks do log auditavel do
  serving com uma referencia (ex.: distribuicao esperada da politica), via PSI
  (Population Stability Index).
- **Monitoramento de recompensa:** acompanha a taxa de recompensa ao longo do tempo a
  partir das recompensas atrasadas (Etapa 2), sinalizando degradacao.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.bandits.environment import SYNTH_DIR
from src.service.audit import DEFAULT_AUDIT_PATH

_EPS = 1e-6


def read_audit_records(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Le todos os registros do log auditavel (JSONL)."""
    audit_path = Path(path) if path else DEFAULT_AUDIT_PATH
    if not audit_path.exists():
        return []
    records = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def decision_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribuicao de bracos, reason codes e taxa de fallback do serving."""
    n = len(records)
    if n == 0:
        return {"n": 0, "arm": {}, "reason": {}, "fallback_rate": 0.0}

    arm_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    fallbacks = 0
    for r in records:
        arm_counts[r["arm_id"]] = arm_counts.get(r["arm_id"], 0) + 1
        for code in r.get("reason_codes", []):
            reason_counts[code] = reason_counts.get(code, 0) + 1
            if code.startswith("SAFE_FALLBACK"):
                fallbacks += 1
    return {
        "n": n,
        "arm": {k: v / n for k, v in arm_counts.items()},
        "reason": {k: v / n for k, v in reason_counts.items()},
        "fallback_rate": fallbacks / n,
    }


def population_stability_index(expected: dict[str, float], observed: dict[str, float]) -> float:
    """PSI entre duas distribuicoes categoricas (fracoes por categoria)."""
    categories = set(expected) | set(observed)
    psi = 0.0
    for cat in categories:
        e = max(expected.get(cat, 0.0), _EPS)
        o = max(observed.get(cat, 0.0), _EPS)
        psi += (o - e) * math.log(o / e)
    return psi


@dataclass
class DriftResult:
    psi: float
    level: str  # "none" | "moderate" | "significant"
    drifted: bool


def classify_drift(psi: float) -> DriftResult:
    """Classifica o PSI: <0.1 estavel, 0.1-0.25 moderado, >0.25 significativo."""
    if psi < 0.1:
        return DriftResult(psi, "none", False)
    if psi < 0.25:
        return DriftResult(psi, "moderate", True)
    return DriftResult(psi, "significant", True)


def detect_decision_drift(
    reference_arm_dist: dict[str, float],
    audit_path: str | Path | None = None,
) -> DriftResult:
    """Drift entre a distribuicao de bracos de referencia e a observada no serving."""
    records = read_audit_records(audit_path)
    observed = decision_distribution(records)["arm"]
    psi = population_stability_index(reference_arm_dist, observed)
    return classify_drift(psi)


def reward_trend(n_bins: int = 5) -> pd.DataFrame:
    """Taxa media de recompensa por janela temporal (monitoramento de recompensa).

    Usa `delayed_rewards.parquet` (Etapa 2), ordenado por `decision_ts`.
    """
    path = SYNTH_DIR / "delayed_rewards.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} ausente (gere a Etapa 2).")
    df = pd.read_parquet(path).sort_values("decision_ts").reset_index(drop=True)
    df["bin"] = pd.qcut(df.index, q=n_bins, labels=[f"w{i+1}" for i in range(n_bins)])
    trend = df.groupby("bin", observed=True)["reward_value"].agg(["mean", "size"]).reset_index()
    trend = trend.rename(columns={"mean": "reward_rate", "size": "n"})
    trend["reward_rate"] = trend["reward_rate"].round(4)
    return trend
