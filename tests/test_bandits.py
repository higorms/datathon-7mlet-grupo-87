"""Testes da camada de bandits (Etapa 3): politicas, ambiente e simulacao."""

from __future__ import annotations

import numpy as np
import pytest

from src.bandits.environment import build_environment_from_catalog
from src.bandits.policies import EpsilonGreedy, FixedArm, ThompsonSampling, UCB1
from src.bandits.simulation import run_episode, run_policy


@pytest.fixture(scope="module")
def env():
    return build_environment_from_catalog()


def test_ambiente_tem_otimo_definido(env):
    """O ambiente deve ter taxas crescentes e um unico braco otimo bem definido."""
    assert env.n_arms >= 2
    assert env.true_p.min() > 0 and env.true_p.max() < 1
    # Braco otimo == argmax e gap positivo para o segundo melhor.
    ordenado = np.sort(env.true_p)
    assert ordenado[-1] > ordenado[-2], "Sem gap entre o melhor e o segundo braco."
    assert env.best_arm == int(np.argmax(env.true_p))


def test_fixed_arm_eh_deterministico(env):
    """Baseline fixo sempre joga o mesmo braco e nunca explora."""
    pol = FixedArm(arm=2)
    pol.reset(env.n_arms)
    rng = np.random.default_rng(0)
    escolhas = {pol.select(rng) for _ in range(50)}
    assert escolhas == {2}
    assert pol.greedy_arm() == 2


def test_thompson_atualiza_posterior():
    """Recompensas positivas aumentam alpha; negativas aumentam beta."""
    ts = ThompsonSampling()
    ts.reset(3)
    ts.update(0, 1.0)
    ts.update(0, 0.0)
    ts.update(1, 1.0)
    assert ts.alpha[0] == 2.0 and ts.beta[0] == 2.0
    assert ts.alpha[1] == 2.0 and ts.beta[1] == 1.0
    assert ts.greedy_arm() == 1  # maior media a posteriori


def test_ucb_cold_start_joga_cada_braco_uma_vez():
    """No cold-start, UCB1 deve cobrir todos os bracos antes de repetir."""
    ucb = UCB1()
    ucb.reset(4)
    rng = np.random.default_rng(0)
    primeiros = []
    for _ in range(4):
        arm = ucb.select(rng)
        primeiros.append(arm)
        ucb.update(arm, 1.0)
    assert sorted(primeiros) == [0, 1, 2, 3]


def test_ucb_formula_favorece_braco_incerto():
    """Com medias iguais, UCB prioriza o braco menos jogado (maior bonus)."""
    ucb = UCB1(c=1.0)
    ucb.reset(2)
    # Braco 0 jogado muitas vezes; braco 1 poucas, mesma media.
    for _ in range(100):
        ucb.update(0, 0.5)
    for _ in range(2):
        ucb.update(1, 0.5)
    rng = np.random.default_rng(0)
    assert ucb.select(rng) == 1


def test_regret_nao_negativo_e_monotono(env):
    """O regret acumulado e nao-negativo e nao-decrescente."""
    res = run_episode(ThompsonSampling(), env, horizon=500, seed=1)
    assert res.cumulative_regret[0] >= 0
    assert np.all(np.diff(res.cumulative_regret) >= -1e-9)
    assert res.cumulative_regret[-1] >= 0


def test_thompson_supera_baseline_fixo(env):
    """Apos muitas rodadas, TS deve ter regret bem menor que o baseline fixo no pior braco."""
    horizon, seeds = 5000, 8
    pior = int(env.true_p.argmin())
    ts = run_policy(lambda: ThompsonSampling(), env, horizon, seeds)
    base = run_policy(lambda: FixedArm(arm=pior), env, horizon, seeds)
    assert ts.final_regret_mean < base.final_regret_mean
    # TS deve concentrar selecao no braco otimo.
    assert ts.optimal_arm_rate > 0.5


def test_reprodutibilidade_mesma_semente(env):
    """Mesma semente -> mesmo resultado (determinismo da simulacao)."""
    a = run_episode(EpsilonGreedy(0.1), env, horizon=300, seed=42)
    b = run_episode(EpsilonGreedy(0.1), env, horizon=300, seed=42)
    assert np.array_equal(a.cumulative_reward, b.cumulative_reward)
    assert np.array_equal(a.arm_counts, b.arm_counts)


def test_feedback_atrasado_nao_reduz_regret(env):
    """Feedback atrasado nao deve melhorar o aprendizado (regret >= imediato)."""
    horizon, seeds = 4000, 8
    imediato = run_policy(lambda: ThompsonSampling(), env, horizon, seeds, mean_delay=0.0)
    atrasado = run_policy(lambda: ThompsonSampling(), env, horizon, seeds, mean_delay=400.0)
    assert atrasado.final_regret_mean >= imediato.final_regret_mean - 1e-6
