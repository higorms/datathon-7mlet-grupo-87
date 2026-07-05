"""Laco de simulacao do bandit com feedback atrasado e metricas (Etapa 3).

Cada episodio roda T rodadas: a politica escolhe um braco, o ambiente sorteia a
recompensa Bernoulli e a observacao e entregue `d` rodadas depois (feedback atrasado).
A politica so e atualizada quando a recompensa chega. Ao final, recompensas pendentes
sao liberadas (flush).

Metricas coletadas por episodio:
    cumulative_reward[t] - soma das recompensas geradas ate t (independente do atraso).
    cumulative_regret[t] - soma de (p* - p_escolhido) ate t.
    exploration[t]       - 1 se o braco escolhido != braco guloso da politica naquele t.
    arm_counts           - quantas vezes cada braco foi escolhido.

`run_experiment` repete o episodio para varias sementes e agrega media e desvio.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.bandits.environment import BanditEnvironment, sample_delay
from src.bandits.policies import Policy


@dataclass
class EpisodeResult:
    cumulative_reward: np.ndarray
    cumulative_regret: np.ndarray
    exploration: np.ndarray  # 0/1 por rodada
    arm_counts: np.ndarray


@dataclass
class PolicyResult:
    name: str
    mean_cum_regret: np.ndarray
    std_cum_regret: np.ndarray
    mean_cum_reward: np.ndarray
    final_regret_mean: float
    final_regret_std: float
    final_reward_mean: float
    conversion_rate: float        # recompensa media por rodada
    exploration_rate: float       # fracao de rodadas exploratorias
    arm_distribution: np.ndarray  # fracao de selecoes por braco
    optimal_arm_rate: float       # fracao de selecoes do braco otimo
    seeds: int = field(default=0)


def run_episode(
    policy: Policy,
    env: BanditEnvironment,
    horizon: int,
    seed: int,
    mean_delay: float = 0.0,
) -> EpisodeResult:
    """Roda um episodio de `horizon` rodadas com a politica e o ambiente dados."""
    rng = np.random.default_rng(seed)
    policy.reset(env.n_arms)

    cum_reward = np.zeros(horizon, dtype=np.float64)
    cum_regret = np.zeros(horizon, dtype=np.float64)
    exploration = np.zeros(horizon, dtype=np.int8)
    arm_counts = np.zeros(env.n_arms, dtype=np.int64)

    # Pre-sorteia os atrasos das observacoes.
    delays = sample_delay(rng, mean_delay, horizon)
    # Buffer de recompensas pendentes, indexado pela rodada de chegada (arrival).
    # pending[a] = observacoes entregues ao FIM da rodada a. O indice `horizon` e o
    # bucket de flush para chegadas alem do horizonte.
    pending: list[list[tuple[int, float]]] = [[] for _ in range(horizon + 1)]

    running_reward = 0.0
    running_regret = 0.0

    for t in range(horizon):
        # 1) Politica decide com base no que ja foi observado ate o fim da rodada t-1.
        greedy = policy.greedy_arm()
        arm = policy.select(rng)
        exploration[t] = int(arm != greedy)
        arm_counts[arm] += 1

        # 2) Ambiente gera a recompensa (existe agora, observada apos o atraso).
        reward = env.pull(arm, rng)
        running_reward += reward
        running_regret += env.regret(arm)
        cum_reward[t] = running_reward
        cum_regret[t] = running_regret

        # 3) Agenda a observacao para a rodada t + d (d=0 => chega ao fim desta rodada).
        arrival = min(t + int(delays[t]), horizon)
        pending[arrival].append((arm, float(reward)))

        # 4) Entrega ao FIM da rodada t tudo que chegou em t (inclui as de d=0 acima).
        if pending[t]:
            for arm_done, reward_done in pending[t]:
                policy.update(arm_done, reward_done)
            pending[t] = []

    # Flush: entrega chegadas alem do horizonte (nao afeta as metricas ja coletadas).
    for arm_done, reward_done in pending[horizon]:
        policy.update(arm_done, reward_done)

    return EpisodeResult(cum_reward, cum_regret, exploration, arm_counts)


def run_policy(
    policy_factory,
    env: BanditEnvironment,
    horizon: int,
    seeds: int,
    mean_delay: float = 0.0,
    base_seed: int = 1000,
) -> PolicyResult:
    """Roda a politica para varias sementes e agrega as metricas.

    `policy_factory` e uma funcao sem argumentos que cria uma instancia nova da politica
    (para nao vazar estado entre sementes).
    """
    all_regret = np.zeros((seeds, horizon))
    all_reward = np.zeros((seeds, horizon))
    all_explore = np.zeros(seeds)
    all_counts = np.zeros((seeds, env.n_arms))

    name = policy_factory().name
    for s in range(seeds):
        res = run_episode(policy_factory(), env, horizon, base_seed + s, mean_delay)
        all_regret[s] = res.cumulative_regret
        all_reward[s] = res.cumulative_reward
        all_explore[s] = res.exploration.mean()
        all_counts[s] = res.arm_counts

    mean_counts = all_counts.mean(axis=0)
    arm_dist = mean_counts / mean_counts.sum()

    return PolicyResult(
        name=name,
        mean_cum_regret=all_regret.mean(axis=0),
        std_cum_regret=all_regret.std(axis=0),
        mean_cum_reward=all_reward.mean(axis=0),
        final_regret_mean=float(all_regret[:, -1].mean()),
        final_regret_std=float(all_regret[:, -1].std()),
        final_reward_mean=float(all_reward[:, -1].mean()),
        conversion_rate=float(all_reward[:, -1].mean() / horizon),
        exploration_rate=float(all_explore.mean()),
        arm_distribution=arm_dist,
        optimal_arm_rate=float(arm_dist[env.best_arm]),
        seeds=seeds,
    )
