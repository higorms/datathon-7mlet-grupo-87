"""Politicas de multi-armed bandit comparadas na Etapa 3.

Interface comum (`Policy`):
    reset(n_arms)        - reinicia o estado interno para um novo episodio.
    select(rng) -> int   - escolhe um braco (indice). `rng` e um numpy Generator.
    update(arm, reward)  - atualiza o estado com a recompensa observada (0/1).
    greedy_arm() -> int  - braco que a politica jogaria por explotacao pura (argmax da
                           estimativa pontual). Usado para medir exploracao:
                           exploracao = (braco_escolhido != greedy_arm()).

Cold-start:
    - ThompsonSampling: prior Beta(1, 1) -> explora naturalmente sem dados.
    - UCB1: joga cada braco uma vez (bonus infinito) antes de comparar.
    - EpsilonGreedy: contagens iniciam em zero; o ramo epsilon garante exploracao.
    - FixedArm: nao precisa (politica nao-adaptativa de controle).
"""

from __future__ import annotations

import numpy as np


class Policy:
    """Classe base. Subclasses implementam select/update/greedy_arm."""

    name: str = "policy"
    is_deterministic: bool = False

    def reset(self, n_arms: int) -> None:
        self.n_arms = n_arms

    def select(self, rng: np.random.Generator) -> int:  # noqa: ARG002
        raise NotImplementedError

    def update(self, arm: int, reward: float) -> None:
        raise NotImplementedError

    def greedy_arm(self) -> int:
        raise NotImplementedError


class FixedArm(Policy):
    """Baseline deterministico: sempre joga o mesmo braco (regra fixa de controle)."""

    is_deterministic = True

    def __init__(self, arm: int = 0, name: str = "Baseline fixo") -> None:
        self.arm = arm
        self.name = name

    def reset(self, n_arms: int) -> None:
        super().reset(n_arms)

    def select(self, rng: np.random.Generator) -> int:  # noqa: ARG002
        return self.arm

    def update(self, arm: int, reward: float) -> None:
        pass

    def greedy_arm(self) -> int:
        return self.arm


class EpsilonGreedy(Policy):
    """Baseline adaptativo simples: explora aleatoriamente com probabilidade epsilon."""

    def __init__(self, epsilon: float = 0.1, name: str | None = None) -> None:
        self.epsilon = epsilon
        self.name = name or f"Epsilon-greedy (eps={epsilon})"

    def reset(self, n_arms: int) -> None:
        super().reset(n_arms)
        self.counts = np.zeros(n_arms, dtype=np.int64)
        self.values = np.zeros(n_arms, dtype=np.float64)

    def select(self, rng: np.random.Generator) -> int:
        if rng.random() < self.epsilon:
            return int(rng.integers(self.n_arms))
        return self.greedy_arm()

    def update(self, arm: int, reward: float) -> None:
        self.counts[arm] += 1
        # Media incremental.
        self.values[arm] += (reward - self.values[arm]) / self.counts[arm]

    def greedy_arm(self) -> int:
        return int(np.argmax(self.values))


class UCB1(Policy):
    """Familia UCB (referencia "Nilos-UCB").

    Indice de selecao: media empirica + bonus de incerteza
        UCB_a = mu_a + c * sqrt( 2 * ln(t) / n_a )
    onde t e o numero total de jogadas e n_a as jogadas do braco a. O termo de bonus
    decresce conforme o braco e explorado, equilibrando confianca e exploracao.
    """

    def __init__(self, c: float = 1.0, name: str | None = None) -> None:
        self.c = c
        self.name = name or ("UCB1 (Nilos-UCB)" if c == 1.0 else f"UCB1 (c={c})")

    def reset(self, n_arms: int) -> None:
        super().reset(n_arms)
        self.counts = np.zeros(n_arms, dtype=np.int64)
        self.values = np.zeros(n_arms, dtype=np.float64)
        self.total = 0

    def select(self, rng: np.random.Generator) -> int:  # noqa: ARG002
        # Cold-start: joga cada braco ao menos uma vez.
        untried = np.where(self.counts == 0)[0]
        if untried.size > 0:
            return int(untried[0])
        bonus = self.c * np.sqrt(2.0 * np.log(self.total) / self.counts)
        return int(np.argmax(self.values + bonus))

    def update(self, arm: int, reward: float) -> None:
        self.counts[arm] += 1
        self.total += 1
        self.values[arm] += (reward - self.values[arm]) / self.counts[arm]

    def greedy_arm(self) -> int:
        return int(np.argmax(self.values))


class ThompsonSampling(Policy):
    """Thompson Sampling bayesiano com prior Beta-Bernoulli.

    Mantem Beta(alpha_a, beta_a) por braco (prior Beta(1, 1) = uniforme). A cada passo
    amostra theta_a ~ Beta(alpha_a, beta_a) e joga argmax_a theta_a. Atualiza
    alpha += reward, beta += 1 - reward.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0,
                 name: str = "Thompson Sampling") -> None:
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.name = name

    def reset(self, n_arms: int) -> None:
        super().reset(n_arms)
        self.alpha = np.full(n_arms, self.prior_alpha, dtype=np.float64)
        self.beta = np.full(n_arms, self.prior_beta, dtype=np.float64)

    def select(self, rng: np.random.Generator) -> int:
        theta = rng.beta(self.alpha, self.beta)
        return int(np.argmax(theta))

    def update(self, arm: int, reward: float) -> None:
        self.alpha[arm] += reward
        self.beta[arm] += 1.0 - reward

    def greedy_arm(self) -> int:
        return int(np.argmax(self.alpha / (self.alpha + self.beta)))
