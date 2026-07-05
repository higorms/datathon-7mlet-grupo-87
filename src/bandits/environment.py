"""Ambiente Bernoulli estacionario para a simulacao de bandit (Etapa 3).

A recompensa-verdade de cada braco e atribuida por **ordem crescente de `base_score`**
do catalogo: o braco de menor base_score recebe MIN_RATE e o de maior recebe MAX_RATE,
interpolando linearmente os intermediarios.

Justificativa: as taxas de conversao *marginais* observadas por braco no log sintetico
sao muito proximas (~11-12%), porque o braco foi atribuido por contexto sobre o desfecho
original (confundimento) — gaps minusculos tornam a comparacao de bandit degenerada.
Usamos a ORDEM do `base_score` (a "forca" projetada de cada oferta) e reescalonamos para
um intervalo com gaps claros e aprendiveis em ~20k rodadas. Assim existe um braco otimo
bem definido (o de maior base_score) e o regret e mensuravel e legivel.

O modelo de feedback atrasado emite a recompensa observada `d` rodadas apos a decisao,
com `d ~ Poisson(mean_delay)` (0 = feedback imediato), representando de forma abstrata as
recompensas atrasadas modeladas em dias na Etapa 2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data.metadata import PROJECT_ROOT

SYNTH_DIR = PROJECT_ROOT / "data" / "synthetic_enrichment"

#: Intervalo das taxas-verdade do ambiente (gaps claros para a comparacao de bandit).
MIN_RATE = 0.04
MAX_RATE = 0.18


@dataclass
class BanditEnvironment:
    """Ambiente Bernoulli multi-braco com recompensa-verdade conhecida."""

    arm_ids: list[str]
    arm_names: list[str]
    true_p: np.ndarray  # probabilidade de recompensa por braco

    @property
    def n_arms(self) -> int:
        return len(self.true_p)

    @property
    def best_arm(self) -> int:
        return int(np.argmax(self.true_p))

    @property
    def best_p(self) -> float:
        return float(np.max(self.true_p))

    def pull(self, arm: int, rng: np.random.Generator) -> int:
        """Sorteia a recompensa Bernoulli do braco escolhido."""
        return int(rng.random() < self.true_p[arm])

    def regret(self, arm: int) -> float:
        """Regret instantaneo (perda em relacao ao melhor braco)."""
        return self.best_p - float(self.true_p[arm])


def load_catalog() -> pd.DataFrame:
    """Carrega o catalogo sintetico, construindo-o se necessario (via notebook nao;
    aqui apenas validamos a presenca do artefato da Etapa 2)."""
    path = SYNTH_DIR / "offer_catalog.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} ausente. Gere a camada sintetica (Etapa 2) antes de rodar a Etapa 3."
        )
    return pd.read_parquet(path)


def build_environment_from_catalog(
    min_rate: float = MIN_RATE, max_rate: float = MAX_RATE
) -> BanditEnvironment:
    """Constroi o ambiente: taxas em [min_rate, max_rate] por ordem de base_score.

    O braco de menor base_score recebe min_rate; o de maior, max_rate; os demais sao
    interpolados linearmente, preservando a ordem do catalogo com gaps uniformes.
    """
    catalog = load_catalog().sort_values("arm_id").reset_index(drop=True)
    n = len(catalog)
    rates_ascending = np.linspace(min_rate, max_rate, n)
    # rank (0 = menor base_score) de cada braco, na ordem por arm_id.
    rank = catalog["base_score"].rank(method="first").astype(int).to_numpy() - 1
    true_p = rates_ascending[rank]
    return BanditEnvironment(
        arm_ids=catalog["arm_id"].tolist(),
        arm_names=catalog["arm_name"].tolist(),
        true_p=true_p,
    )


def sample_delay(rng: np.random.Generator, mean_delay: float, size: int) -> np.ndarray:
    """Atraso (em rodadas) da observacao da recompensa. mean_delay=0 => imediato."""
    if mean_delay <= 0:
        return np.zeros(size, dtype=np.int64)
    return rng.poisson(mean_delay, size=size).astype(np.int64)
