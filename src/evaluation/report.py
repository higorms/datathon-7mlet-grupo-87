"""Geracao de relatorio markdown e metricas JSON da Etapa 4."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")

from src.bandits.environment import build_environment_from_catalog
from src.bandits.simulation import PolicyResult
from src.data.metadata import PROJECT_ROOT
from src.evaluation.evaluator import GoldenSetResult
from src.evaluation.fairness import FairnessResult, fairness_summary_table
from src.evaluation.golden_set import coverage_summary, load_golden_cases
from src.evaluation.sensitivity import SensitivityRow

REPORTS_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"


def plot_sensitivity(rows: list[SensitivityRow], output: Path) -> None:
    """Grafico de regret por variacao de parametro."""
    df = pd.DataFrame([r.__dict__ for r in rows])
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("horizon", "horizon"),
        ("mean_delay", "mean_delay"),
        ("ts_prior", "ts_prior"),
        ("ucb_c", "ucb_c"),
    ]
    for ax, (param, title) in zip(axes.flat, panels):
        sub = df[df["parameter"] == param]
        if sub.empty:
            ax.set_visible(False)
            continue
        for policy, grp in sub.groupby("policy"):
            ax.plot(range(len(grp)), grp["final_regret_mean"].to_numpy(), marker="o", label=policy)
        ax.set_xticks(range(len(sub["value"].unique())))
        ax.set_xticklabels([str(v) for v in sub["value"].unique()], rotation=20, fontsize=8)
        ax.set_title(f"Sensibilidade: {title}")
        ax.set_ylabel("regret final")
        ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()


def plot_fairness(fairness: dict[str, FairnessResult], output: Path) -> None:
    """Heatmap de exposicao observada vs. gulosa por segmento."""
    col = "segment_macro_regime"
    if col not in fairness:
        col = next(iter(fairness))
    res = fairness[col]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    sns.heatmap(res.exposure_matrix, annot=True, fmt=".2f", cmap="Blues", ax=axes[0])
    axes[0].set_title(f"Exposicao observada ({col})")
    sns.heatmap(res.greedy_matrix, annot=True, fmt=".2f", cmap="Greens", ax=axes[1])
    axes[1].set_title(f"Referencia gulosa ({col})")
    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()


def render_report(
    golden: GoldenSetResult,
    bandit_results: list[PolicyResult],
    sensitivity: list[SensitivityRow],
    fairness: dict[str, FairnessResult],
    horizon: int,
    seeds: int,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cases = load_golden_cases()
    coverage = coverage_summary(cases)

    golden_rows = "\n".join(
        f"| {r.case.case_id} | {r.case.category} | {r.predicted_arm_id} | "
        f"{r.case.expected_arm_id} | {'PASS' if r.passed else 'FAIL'} |"
        for r in golden.results
    )

    bandit_rows = "\n".join(
        f"| {r.name} | {r.final_reward_mean:.0f} | {r.conversion_rate*100:.2f}% | "
        f"{r.final_regret_mean:.1f} ± {r.final_regret_std:.1f} | "
        f"{r.exploration_rate*100:.1f}% | {r.optimal_arm_rate*100:.1f}% |"
        for r in bandit_results
    )

    cat_rows = "\n".join(
        f"| {cat} | {rate*100:.1f}% |"
        for cat, rate in sorted(golden.pass_rate_by_category.items())
    )

    sens_rows = "\n".join(
        f"| {r.parameter} | {r.value} | {r.policy} | {r.final_regret_mean:.1f} | "
        f"{r.conversion_rate*100:.2f}% | {r.optimal_arm_rate*100:.1f}% |"
        for r in sensitivity
    )

    fair_df = fairness_summary_table(fairness)
    fair_rows = "\n".join(
        f"| {row['segmento']} | {row['n_grupos']} | {row['max_min_ratio_otimo']} | "
        f"{row['std_exposicao_otimo']} |"
        for _, row in fair_df.iterrows()
    )

    failures = golden.failures
    fail_block = ""
    if failures:
        fail_block = "\n".join(
            f"- **{f.case.case_id}**: {f.failure_reason}" for f in failures
        )
    else:
        fail_block = "_Nenhuma falha._"

    ts = next(r for r in bandit_results if "Thompson" in r.name and "Beta" not in r.name)
    baseline = bandit_results[0]

    return f"""# Avaliacao offline — Etapa 4 (golden set + metricas)

> Gerado por `src/evaluation` em {generated}.
> Reproduza com: `poetry run python -m src.evaluation`.
> Configuracao bandit: horizonte = {horizon}, {seeds} sementes.

## 1. Golden set

Arquivo versionado: `data/golden_set/evaluation_cases.jsonl` ({len(cases)} casos).

| Categoria | Casos |
| --- | --- |
{chr(10).join(f'| {k} | {v} |' for k, v in sorted(coverage.items()))}

**Pass rate global: {golden.pass_rate*100:.1f}%** ({sum(r.passed for r in golden.results)}/{len(golden.results)})

| Categoria | Pass rate |
| --- | --- |
{cat_rows}

### Resultados por caso

| case_id | categoria | previsto | esperado | status |
| --- | --- | --- | --- | --- |
{golden_rows}

### Falhas
{fail_block}

## 2. Matriz de metricas (politicas bandit — Etapa 3)

Politica candidata a serving (Etapa 5): **Thompson Sampling** — menor regret ({ts.final_regret_mean:.1f}) e maior % no braco otimo ({ts.optimal_arm_rate*100:.1f}%) frente ao baseline fixo ({baseline.final_regret_mean:.1f}).

| Politica | Recompensa | Conversao | Regret final | Exploracao | % braco otimo |
| --- | --- | --- | --- | --- | --- |
{bandit_rows}

## 3. Analise de sensibilidade

| Parametro | Valor | Politica | Regret | Conversao | % otimo |
| --- | --- | --- | --- | --- | --- |
{sens_rows}

Figura: `reports/figures/offline_sensitivity.png`.

## 4. Fairness de exposicao entre segmentos

Compara distribuicao **observada** (eventos sinteticos) com referencia **gulosa** (sem exploracao estocastica).

| Dimensao | Grupos | Max/min ratio (otimo) | Std exposicao otimo |
| --- | --- | --- | --- |
{fair_rows}

Figura: `reports/figures/offline_fairness_exposure.png`.

> Ratio max/min elevado indica desigualdade de exposicao ao braço otimo (`arm_rate_boost`) entre segmentos — revisar caps de exploracao antes do serving.

## 5. Limitacoes, vieses e condicoes de nao-uso

### Limitacoes
- Base **sintetica e estatica** (Bank Marketing 2008–2013); scores contextuais nao sao causais.
- **Desbalanceamento** de conversao (~11,7%) — metricas de acuracia sao insuficientes.
- Simulacao bandit (Etapa 3) e **nao-contextual**; golden set avalia roteamento contextual — camadas distintas complementares.
- Fairness calculada sobre amostra de eventos; segmentos raros tem alta variancia.

### Vieses identificados
- Celular infla sistematicamente `arm_rate_boost` (incentivo financeiro).
- Cold-start sem trilho de seguranca tende a ofertas agressivas — mitigado por casos adversariais.
- Exploracao do Thompson Sampling pode super-expor braços sub-otimos em segmentos vulneraveis.

### Quando NAO usar a politica automaticamente
- Contexto **incompleto** (canal desconhecido, flags de fallback) → usar `arm_control`.
- **Macro stress** + jovem + cold-start sem historico → revisao humana obrigatoria.
- Cliente **nao elegivel** a incentivo financeiro (`financial_incentive_blocked`) → nunca `arm_rate_boost`.
- Segmentos com **sub-exposicao** ao braço adequado (ver fairness) → cap de exploracao ou politica segmentada.
- Ambiente com **feedback altamente atrasado** (delay > 200 rodadas) → degradacao mensuravel do regret.

### Figuras
- `reports/figures/offline_sensitivity.png`
- `reports/figures/offline_fairness_exposure.png`
"""


def write_metrics_json(
    golden: GoldenSetResult,
    bandit_results: list[PolicyResult],
    sensitivity: list[SensitivityRow],
    fairness: dict[str, FairnessResult],
    horizon: int,
    seeds: int,
    output: Path,
) -> None:
    env = build_environment_from_catalog()
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "horizon": horizon,
        "seeds": seeds,
        "golden_set": {
            "n_cases": len(golden.results),
            "pass_rate": golden.pass_rate,
            "pass_rate_by_category": golden.pass_rate_by_category,
            "failures": [
                {"case_id": f.case.case_id, "reason": f.failure_reason}
                for f in golden.failures
            ],
        },
        "bandit_matrix": [
            {
                "policy": r.name,
                "final_regret_mean": r.final_regret_mean,
                "conversion_rate": r.conversion_rate,
                "exploration_rate": r.exploration_rate,
                "optimal_arm_rate": r.optimal_arm_rate,
            }
            for r in bandit_results
        ],
        "sensitivity": [r.__dict__ for r in sensitivity],
        "fairness": fairness_summary_table(fairness).to_dict(orient="records"),
        "environment": {
            "arm_ids": env.arm_ids,
            "true_p": env.true_p.tolist(),
        },
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
