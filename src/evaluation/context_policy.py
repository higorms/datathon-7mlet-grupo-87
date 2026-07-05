"""Politica contextual deterministica extraida da Etapa 2.

Replica os pesos de score do notebook `02_enriquecimento_sintetico.ipynb` para
avaliacao offline caso a caso e analise de fairness. A ordem dos bracos segue
a ordem do catalogo em `offer_catalog.parquet` (nao ordenacao alfabetica).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from src.bandits.environment import SYNTH_DIR
from src.data.metadata import PDAYS_NOT_CONTACTED

POLICY_TEMPERATURE: float = 0.75
PEAK_MONTHS: frozenset[str] = frozenset({"mar", "apr", "sep", "oct", "dec"})
VALID_CONTACTS: frozenset[str] = frozenset({"cellular", "telephone"})


@lru_cache(maxsize=1)
def load_arm_ids() -> tuple[str, ...]:
    """IDs dos bracos na ordem do catalogo (indice = coluna do score)."""
    path = SYNTH_DIR / "offer_catalog.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} ausente. Gere a camada sintetica (Etapa 2) antes da Etapa 4."
        )
    catalog = pd.read_parquet(path)
    return tuple(catalog["arm_id"].tolist())


def _feature_vector(context: dict[str, Any]) -> dict[str, float]:
    """Extrai features numericas a partir de um contexto de decisao."""
    age = float(context.get("age", 40))
    pdays = float(context.get("pdays", PDAYS_NOT_CONTACTED))
    previous = float(context.get("previous", 0))
    contact = str(context.get("contact", "unknown"))
    poutcome = str(context.get("poutcome", "unknown"))
    job = str(context.get("job", "unknown"))
    month = str(context.get("month", "may"))
    macro = str(context.get("segment_macro_regime", "neutral"))

    young = float(age < 35)
    mid = float(35 <= age < 55)
    cellular = float(contact == "cellular")
    telephone = float(contact == "telephone")
    success = float(poutcome == "success")
    repeat_contact = float(pdays != PDAYS_NOT_CONTACTED)
    previous_contact = float(previous > 0)
    student = float(job == "student")
    retired = float(job == "retired")
    month_peak = float(month in PEAK_MONTHS)
    macro_stress = float(macro == "stress")
    macro_tight = float(macro == "tight")

    return {
        "young": young,
        "mid": mid,
        "cellular": cellular,
        "telephone": telephone,
        "success": success,
        "repeat_contact": repeat_contact,
        "previous_contact": previous_contact,
        "student": student,
        "retired": retired,
        "month_peak": month_peak,
        "macro_stress": macro_stress,
        "macro_tight": macro_tight,
    }


def compute_arm_scores(context: dict[str, Any]) -> np.ndarray:
    """Retorna vetor de scores (5 bracos) para o contexto dado."""
    f = _feature_vector(context)
    return np.array(
        [
            0.10 + 0.10 * f["repeat_contact"] + 0.05 * f["macro_stress"],
            0.28
            + 0.35 * f["cellular"]
            + 0.20 * f["success"]
            + 0.12 * f["macro_tight"]
            + 0.08 * f["young"],
            0.24
            + 0.25 * f["young"]
            + 0.20 * f["cellular"]
            + 0.10 * f["month_peak"]
            + 0.10 * f["student"],
            0.26
            + 0.25 * f["telephone"]
            + 0.15 * f["repeat_contact"]
            + 0.18 * f["success"]
            + 0.12 * f["retired"],
            0.22
            + 0.20 * f["mid"]
            + 0.12 * f["previous_contact"]
            + 0.08 * f["macro_stress"]
            + 0.08 * f["month_peak"],
        ],
        dtype=np.float64,
    )


def compute_selection_probabilities(scores: np.ndarray) -> np.ndarray:
    """Converte scores em probabilidades softmax (mesma formula da Etapa 2)."""
    shifted = scores / POLICY_TEMPERATURE
    shifted = shifted - shifted.max()
    weights = np.exp(shifted)
    return weights / weights.sum()


def greedy_arm_index(context: dict[str, Any]) -> int:
    """Indice do braco com maior score (politica gulosa deterministica)."""
    return int(np.argmax(compute_arm_scores(context)))


def greedy_arm_id(context: dict[str, Any]) -> str:
    """arm_id do braco guloso para o contexto."""
    arm_ids = load_arm_ids()
    return arm_ids[greedy_arm_index(context)]


def safety_rail_arm(context: dict[str, Any]) -> str | None:
    """Retorna arm_control se o contexto exige fallback seguro; senao None."""
    contact = str(context.get("contact", "unknown"))
    if contact not in VALID_CONTACTS:
        return "arm_control"

    if context.get("force_safe_fallback"):
        return "arm_control"

    pdays = float(context.get("pdays", PDAYS_NOT_CONTACTED))
    macro = str(context.get("segment_macro_regime", "neutral"))
    poutcome = str(context.get("poutcome", "unknown"))
    age = float(context.get("age", 40))

    # Perfil de alto risco regulado: jovem, cold-start e macro stress sem historico.
    if macro == "stress" and pdays == PDAYS_NOT_CONTACTED and age < 30 and poutcome == "unknown":
        return "arm_control"

    return None


def decide_arm(context: dict[str, Any]) -> str:
    """Decisao final: trilhos de seguranca + politica gulosa contextual."""
    safe = safety_rail_arm(context)
    if safe is not None:
        return safe

    blocked = context.get("financial_incentive_blocked")
    arm = greedy_arm_id(context)
    if blocked and arm == "arm_rate_boost":
        return "arm_retention_plus"
    return arm


def score_matrix(df: pd.DataFrame) -> np.ndarray:
    """Matriz de scores (n_linhas x n_bracos) para um DataFrame de contextos."""
    rows = []
    for _, row in df.iterrows():
        ctx = row.to_dict()
        rows.append(compute_arm_scores(ctx))
    return np.vstack(rows)
