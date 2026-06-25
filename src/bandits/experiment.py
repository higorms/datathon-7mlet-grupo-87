"""Experimento comparativo da Etapa 3: baseline x UCB x Thompson Sampling.

Roda as politicas no mesmo ambiente (recompensa-verdade do catalogo sintetico),
calcula recompensa, regret, exploracao e conversao, estuda o efeito de feedback
atrasado e gera figuras + um relatorio markdown reproduzivel.

Uso:
    poetry run python -m src.bandits.experiment            # padrao
    poetry run python -m src.bandits.experiment --horizon 20000 --seeds 30
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.bandits.environment import (  # noqa: E402
    MAX_RATE,
    MIN_RATE,
    BanditEnvironment,
    build_environment_from_catalog,
)
from src.bandits.policies import (  # noqa: E402
    EpsilonGreedy,
    FixedArm,
    ThompsonSampling,
    UCB1,
)
from src.bandits.simulation import PolicyResult, run_policy  # noqa: E402
from src.data.metadata import PROJECT_ROOT  # noqa: E402

logger = logging.getLogger(__name__)

REPORTS_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"


def policy_factories(env: BanditEnvironment):
    """Fabricas das politicas comparadas (control = braco de menor base_score)."""
    control_arm = int(env.true_p.argmin())  # arm_control (benchmark/regra fixa)
    return [
        lambda: FixedArm(arm=control_arm, name="Baseline fixo (controle)"),
        lambda: EpsilonGreedy(epsilon=0.1),
        lambda: UCB1(c=1.0),
        lambda: ThompsonSampling(),
    ]


def run_comparison(env, horizon, seeds, mean_delay=0.0) -> list[PolicyResult]:
    results = []
    for factory in policy_factories(env):
        res = run_policy(factory, env, horizon, seeds, mean_delay=mean_delay)
        logger.info(
            "%-26s regret=%8.1f  conv=%.4f  explor=%.3f  otimo=%.3f",
            res.name, res.final_regret_mean, res.conversion_rate,
            res.exploration_rate, res.optimal_arm_rate,
        )
        results.append(res)
    return results


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def plot_regret(results: list[PolicyResult], horizon: int) -> None:
    plt.figure(figsize=(9, 5))
    for r in results:
        plt.plot(r.mean_cum_regret, label=r.name)
        plt.fill_between(
            range(horizon),
            r.mean_cum_regret - r.std_cum_regret,
            r.mean_cum_regret + r.std_cum_regret,
            alpha=0.12,
        )
    plt.xlabel("rodada")
    plt.ylabel("regret acumulado")
    plt.title("Regret acumulado por politica (media +/- desvio entre sementes)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bandit_regret.png", bbox_inches="tight")
    plt.close()


def plot_reward(results: list[PolicyResult], env: BanditEnvironment, horizon: int) -> None:
    plt.figure(figsize=(9, 5))
    for r in results:
        plt.plot(r.mean_cum_reward, label=r.name)
    # Teto (oraculo): melhor braco jogado sempre.
    plt.plot(range(horizon), env.best_p * np.arange(1, horizon + 1), "k--", lw=1,
             label="oraculo (melhor braco)")
    plt.xlabel("rodada")
    plt.ylabel("recompensa acumulada")
    plt.title("Recompensa acumulada por politica")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bandit_reward.png", bbox_inches="tight")
    plt.close()


def plot_arm_distribution(results: list[PolicyResult], env: BanditEnvironment) -> None:
    _, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(env.n_arms)
    width = 0.8 / len(results)
    for i, r in enumerate(results):
        ax.bar(x + i * width, r.arm_distribution * 100, width, label=r.name)
    ax.set_xticks(x + 0.4 - width / 2)
    ax.set_xticklabels([f"{n}\n(p={p:.3f})" for n, p in zip(env.arm_names, env.true_p)],
                       fontsize=8, rotation=15)
    ax.axvline(env.best_arm + 0.4 - width / 2, color="green", ls=":", lw=1)
    ax.set_ylabel("% de selecoes")
    ax.set_title("Distribuicao de selecao por braco (verde = otimo)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bandit_arm_distribution.png", bbox_inches="tight")
    plt.close()


def plot_delay_study(study: dict) -> None:
    plt.figure(figsize=(9, 5))
    styles = {"imediato": "-", "atrasado": "--"}
    for (name, scenario), r in study.items():
        plt.plot(r.mean_cum_regret, styles[scenario], label=f"{name} ({scenario})")
    plt.xlabel("rodada")
    plt.ylabel("regret acumulado")
    plt.title("Impacto do feedback atrasado no regret")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bandit_delay_study.png", bbox_inches="tight")
    plt.close()


# --------------------------------------------------------------------------- #
# Relatorio
# --------------------------------------------------------------------------- #
def render_report(env, results, study, horizon, seeds, mean_delay) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    arms_tbl = "\n".join(
        f"| {aid} | {an} | {p:.3f} |" + (" **otimo**" if i == env.best_arm else "")
        for i, (aid, an, p) in enumerate(zip(env.arm_ids, env.arm_names, env.true_p))
    )
    comp_rows = "\n".join(
        f"| {r.name} | {r.final_reward_mean:.0f} | {r.conversion_rate*100:.2f}% | "
        f"{r.final_regret_mean:.1f} ± {r.final_regret_std:.1f} | "
        f"{r.exploration_rate*100:.1f}% | {r.optimal_arm_rate*100:.1f}% |"
        for r in results
    )
    baseline = results[0]
    ts = next(r for r in results if "Thompson" in r.name)
    ucb = next(r for r in results if "UCB" in r.name)
    best_adaptive = min((ts, ucb), key=lambda r: r.final_regret_mean)
    regret_reduction = (1 - best_adaptive.final_regret_mean / baseline.final_regret_mean) * 100

    delay_rows = "\n".join(
        f"| {name} | {scenario} | {r.final_regret_mean:.1f} | {r.conversion_rate*100:.2f}% |"
        for (name, scenario), r in study.items()
    )

    return f"""# Comparacao de politicas - Etapa 3 (baseline x bandit)

> Gerado por `src/bandits/experiment.py` em {generated}.
> Reproduza com: `poetry run python -m src.bandits.experiment`.
> Configuracao: horizonte = {horizon} rodadas, {seeds} sementes, atraso medio (cenario
> atrasado) = {mean_delay} rodadas.

## 1. Ambiente de simulacao

Bernoulli estacionario com recompensa-verdade atribuida por ordem de `base_score` do
catalogo (Etapa 2), reescalonada para `[{MIN_RATE}, {MAX_RATE}]` com gaps uniformes.
Justificativa em `src/bandits/environment.py` (as taxas marginais por braco no log sao
quase iguais por confundimento; usar a ORDEM do `base_score` da um braco otimo bem
definido e regret mensuravel).

| arm_id | nome | true_p | |
| --- | --- | --- | --- |
{arms_tbl}

Braco otimo: **{env.arm_names[env.best_arm]}** (p = {env.best_p:.3f}).

## 2. Algoritmos comparados

- **Baseline fixo (controle):** regra deterministica, sempre joga o braco de controle.
- **Epsilon-greedy (eps=0.1):** baseline adaptativo simples.
- **UCB1 (familia Nilos-UCB):** indice `mu_a + sqrt(2 ln t / n_a)` (ver secao 5).
- **Thompson Sampling:** bayesiano Beta-Bernoulli, prior Beta(1,1).

## 3. Resultados (feedback imediato, media de {seeds} sementes)

| Politica | Recompensa | Conversao | Regret final | Exploracao | % braco otimo |
| --- | --- | --- | --- | --- | --- |
{comp_rows}

> A melhor politica adaptativa (**{best_adaptive.name}**) reduz o regret final em
> **{regret_reduction:.1f}%** frente ao baseline fixo, convergindo para o braco otimo.

## 4. Cold-start

- **Thompson Sampling:** prior Beta(1,1) -> amostra com alta variancia quando ha poucos
  dados, explorando naturalmente; a variancia cai conforme `alpha`/`beta` crescem.
- **UCB1:** joga cada braco uma vez (bonus infinito) e depois favorece bracos pouco
  testados via o termo de incerteza.
- **Baselines:** o fixo nao tem cold-start (nao aprende); o epsilon-greedy cobre o
  inicio pelo ramo aleatorio.

## 5. UCB / "Nilos-UCB" (familia UCB)

Implementamos **UCB1** como representante da familia UCB referida como *Nilos-UCB*:

```
UCB_a(t) = mu_a + c * sqrt( 2 * ln(t) / n_a )
```

- `mu_a`: recompensa media empirica do braco a (explotacao).
- `sqrt(2 ln t / n_a)`: bonus de incerteza (exploracao) — cresce com `t` e cai com `n_a`.
- `c`: controla o trade-off confianca/exploracao (usamos `c = 1.0`).

Trade-off: bracos pouco jogados recebem bonus alto e sao reexplorados; conforme `n_a`
cresce, o bonus encolhe e a decisao tende a explotacao do melhor braco. Para contextos,
a extensao natural e **LinUCB** (bonus sobre um modelo linear do contexto) — candidato
para uma etapa contextual futura.

## 6. Recompensas atrasadas

A recompensa e observada `d ~ Poisson(media)` rodadas apos a decisao; a politica so
atualiza ao receber a observacao. Comparacao imediato x atrasado:

| Politica | Cenario | Regret final | Conversao |
| --- | --- | --- | --- |
{delay_rows}

> O atraso retarda o aprendizado (a politica decide mais tempo com informacao
> desatualizada), aumentando o regret. Na Etapa 2 o atraso e modelado em dias com
> censura por horizonte; aqui ele e abstraido em rodadas para o estudo de sensibilidade.

## 7. Conclusao

- Politicas adaptativas (TS e UCB) superam o baseline fixo em recompensa e regret,
  concentrando selecao no braco otimo — evidencia quantitativa do ganho da abordagem
  multi-armed bandit sobre regras fixas.
- Thompson Sampling e UCB1 tratam cold-start de formas distintas (prior bayesiano x
  otimismo sob incerteza), ambas eficazes.
- Feedback atrasado degrada o desempenho de forma mensuravel, motivando o tratamento
  explicito de recompensas atrasadas no serving (Etapas 5 e 7).

### Figuras
- `reports/figures/bandit_regret.png` — regret acumulado.
- `reports/figures/bandit_reward.png` — recompensa acumulada vs oraculo.
- `reports/figures/bandit_arm_distribution.png` — selecao por braco.
- `reports/figures/bandit_delay_study.png` — efeito do feedback atrasado.
"""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Experimento de bandit da Etapa 3.")
    parser.add_argument("--horizon", type=int, default=20000)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--mean-delay", type=float, default=500.0,
                        help="Atraso medio (rodadas) do cenario atrasado.")
    args = parser.parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    env = build_environment_from_catalog()
    logger.info("Ambiente: %d bracos | otimo=%s p=%.3f",
                env.n_arms, env.arm_names[env.best_arm], env.best_p)

    logger.info("== Comparacao principal (feedback imediato) ==")
    results = run_comparison(env, args.horizon, args.seeds, mean_delay=0.0)

    logger.info("== Estudo de feedback atrasado (TS e UCB) ==")
    study: dict[tuple[str, str], PolicyResult] = {}
    for factory in policy_factories(env):
        p = factory()
        if not ("Thompson" in p.name or "UCB" in p.name):
            continue
        short = "Thompson" if "Thompson" in p.name else "UCB1"
        study[(short, "imediato")] = run_policy(factory, env, args.horizon, args.seeds, 0.0)
        study[(short, "atrasado")] = run_policy(factory, env, args.horizon, args.seeds, args.mean_delay)

    plot_regret(results, args.horizon)
    plot_reward(results, env, args.horizon)
    plot_arm_distribution(results, env)
    plot_delay_study(study)

    report = render_report(env, results, study, args.horizon, args.seeds, args.mean_delay)
    (REPORTS_DIR / "bandit-comparison.md").write_text(report, encoding="utf-8")

    # Resumo de metricas em JSON (rastreavel).
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "horizon": args.horizon, "seeds": args.seeds, "mean_delay": args.mean_delay,
        "min_rate": MIN_RATE, "max_rate": MAX_RATE,
        "environment": {
            "arm_ids": env.arm_ids, "true_p": env.true_p.tolist(),
            "best_arm": env.arm_ids[env.best_arm],
        },
        "results": [
            {
                "policy": r.name, "final_regret_mean": r.final_regret_mean,
                "final_regret_std": r.final_regret_std, "conversion_rate": r.conversion_rate,
                "exploration_rate": r.exploration_rate, "optimal_arm_rate": r.optimal_arm_rate,
            }
            for r in results
        ],
    }
    (REPORTS_DIR / "bandit-metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== Etapa 3 concluida ===")
    for r in results:
        print(f"  {r.name:28s} regret={r.final_regret_mean:8.1f}  conv={r.conversion_rate*100:5.2f}%"
              f"  otimo={r.optimal_arm_rate*100:5.1f}%")
    print("Artefatos: reports/bandit-comparison.md, reports/bandit-metrics.json, reports/figures/bandit_*.png")


if __name__ == "__main__":
    main()
