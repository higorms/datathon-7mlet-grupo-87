# Avaliacao offline — Etapa 4 (golden set + metricas)

> Gerado por `src/evaluation` em 2026-07-05 23:42 UTC.
> Reproduza com: `poetry run python -m src.evaluation`.
> Configuracao bandit: horizonte = 10000, 15 sementes.

## 1. Golden set

Arquivo versionado: `data/golden_set/evaluation_cases.jsonl` (24 casos).

| Categoria | Casos |
| --- | --- |
| adversarial | 6 |
| edge | 6 |
| segment | 6 |
| typical | 6 |

**Pass rate global: 100.0%** (24/24)

| Categoria | Pass rate |
| --- | --- |
| adversarial | 100.0% |
| edge | 100.0% |
| segment | 100.0% |
| typical | 100.0% |

### Resultados por caso

| case_id | categoria | previsto | esperado | status |
| --- | --- | --- | --- | --- |
| GS-T01 | typical | arm_rate_boost | arm_rate_boost | PASS |
| GS-T02 | typical | arm_digital_bundle | arm_digital_bundle | PASS |
| GS-T03 | typical | arm_consultative_call | arm_consultative_call | PASS |
| GS-T04 | typical | arm_rate_boost | arm_rate_boost | PASS |
| GS-T05 | typical | arm_consultative_call | arm_consultative_call | PASS |
| GS-T06 | typical | arm_rate_boost | arm_rate_boost | PASS |
| GS-E01 | edge | arm_rate_boost | arm_rate_boost | PASS |
| GS-E02 | edge | arm_consultative_call | arm_consultative_call | PASS |
| GS-E03 | edge | arm_rate_boost | arm_rate_boost | PASS |
| GS-E04 | edge | arm_consultative_call | arm_consultative_call | PASS |
| GS-E05 | edge | arm_rate_boost | arm_rate_boost | PASS |
| GS-E06 | edge | arm_consultative_call | arm_consultative_call | PASS |
| GS-S01 | segment | arm_retention_plus | arm_retention_plus | PASS |
| GS-S02 | segment | arm_rate_boost | arm_rate_boost | PASS |
| GS-S03 | segment | arm_rate_boost | arm_rate_boost | PASS |
| GS-S04 | segment | arm_consultative_call | arm_consultative_call | PASS |
| GS-S05 | segment | arm_digital_bundle | arm_digital_bundle | PASS |
| GS-S06 | segment | arm_rate_boost | arm_rate_boost | PASS |
| GS-A01 | adversarial | arm_control | arm_control | PASS |
| GS-A02 | adversarial | arm_control | arm_control | PASS |
| GS-A03 | adversarial | arm_control | arm_control | PASS |
| GS-A04 | adversarial | arm_retention_plus | arm_retention_plus | PASS |
| GS-A05 | adversarial | arm_control | arm_control | PASS |
| GS-A06 | adversarial | arm_control | arm_control | PASS |

### Falhas
_Nenhuma falha._

## 2. Matriz de metricas (politicas bandit — Etapa 3)

Politica candidata a serving (Etapa 5): **Thompson Sampling** — menor regret (56.6) e maior % no braco otimo (90.2%) frente ao baseline fixo (1400.0).

| Politica | Recompensa | Conversao | Regret final | Exploracao | % braco otimo |
| --- | --- | --- | --- | --- | --- |
| Baseline fixo (controle) | 403 | 4.03% | 1400.0 ± 0.0 | 0.0% | 0.0% |
| Epsilon-greedy (eps=0.1) | 1645 | 16.45% | 147.7 ± 93.9 | 8.0% | 70.1% |
| UCB1 (Nilos-UCB) | 1514 | 15.14% | 293.9 ± 26.2 | 44.6% | 55.0% |
| Thompson Sampling | 1738 | 17.38% | 56.6 ± 15.7 | 9.0% | 90.2% |

## 3. Analise de sensibilidade

| Parametro | Valor | Politica | Regret | Conversao | % otimo |
| --- | --- | --- | --- | --- | --- |
| horizon | 5000 | Thompson Sampling | 55.0 | 16.95% | 81.9% |
| horizon | 10000 | Thompson Sampling | 64.2 | 17.38% | 89.2% |
| horizon | 20000 | Thompson Sampling | 72.8 | 17.66% | 93.8% |
| mean_delay | 0.0 | Thompson Sampling | 55.0 | 16.95% | 81.9% |
| mean_delay | 200.0 | Thompson Sampling | 51.8 | 16.95% | 83.7% |
| mean_delay | 500.0 | Thompson Sampling | 60.8 | 17.12% | 82.9% |
| ts_prior | Beta(1,1) | Thompson Sampling Beta(1,1) | 55.0 | 16.95% | 81.9% |
| ts_prior | Beta(2,2) | Thompson Sampling Beta(2,2) | 57.4 | 16.86% | 79.7% |
| ucb_c | 0.5 | UCB1 (c=0.5) | 105.6 | 15.71% | 66.9% |
| ucb_c | 1.0 | UCB1 (Nilos-UCB) | 188.8 | 14.11% | 45.2% |
| ucb_c | 2.0 | UCB1 (c=2.0) | 261.3 | 12.70% | 32.1% |

Figura: `reports/figures/offline_sensitivity.png`.

## 4. Fairness de exposicao entre segmentos

Compara distribuicao **observada** (eventos sinteticos) com referencia **gulosa** (sem exploracao estocastica).

| Dimensao | Grupos | Max/min ratio (otimo) | Std exposicao otimo |
| --- | --- | --- | --- |
| segment_age_band | 6 | 1.257 | 0.0299 |
| segment_history | 2 | 1.028 | 0.005 |
| segment_macro_regime | 3 | 1.043 | 0.0055 |

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
