# Comparacao de politicas - Etapa 3 (baseline x bandit)

> Gerado por `src/bandits/experiment.py` em 2026-06-25 16:41 UTC.
> Reproduza com: `poetry run python -m src.bandits.experiment`.
> Configuracao: horizonte = 20000 rodadas, 30 sementes, atraso medio (cenario
> atrasado) = 500.0 rodadas.

## 1. Ambiente de simulacao

Bernoulli estacionario com recompensa-verdade atribuida por ordem de `base_score` do
catalogo (Etapa 2), reescalonada para `[0.04, 0.18]` com gaps uniformes.
Justificativa em `src/bandits/environment.py` (as taxas marginais por braco no log sao
quase iguais por confundimento; usar a ORDEM do `base_score` da um braco otimo bem
definido e regret mensuravel).

| arm_id | nome | true_p | |
| --- | --- | --- | --- |
| arm_consultative_call | Contato consultivo | 0.145 |
| arm_control | Mensagem neutra | 0.040 |
| arm_digital_bundle | Pacote digital | 0.110 |
| arm_rate_boost | Taxa bonificada | 0.180 | **otimo**
| arm_retention_plus | Oferta de relacionamento | 0.075 |

Braco otimo: **Taxa bonificada** (p = 0.180).

## 2. Algoritmos comparados

- **Baseline fixo (controle):** regra deterministica, sempre joga o braco de controle.
- **Epsilon-greedy (eps=0.1):** baseline adaptativo simples.
- **UCB1 (familia Nilos-UCB):** indice `mu_a + sqrt(2 ln t / n_a)` (ver secao 5).
- **Thompson Sampling:** bayesiano Beta-Bernoulli, prior Beta(1,1).

## 3. Resultados (feedback imediato, media de 30 sementes)

| Politica | Recompensa | Conversao | Regret final | Exploracao | % braco otimo |
| --- | --- | --- | --- | --- | --- |
| Baseline fixo (controle) | 805 | 4.03% | 2800.0 ± 0.0 | 0.0% | 0.0% |
| Epsilon-greedy (eps=0.1) | 3382 | 16.91% | 208.6 ± 84.2 | 8.0% | 82.3% |
| UCB1 (Nilos-UCB) | 3161 | 15.81% | 432.4 ± 36.9 | 34.5% | 65.3% |
| Thompson Sampling | 3534 | 17.67% | 67.0 ± 19.7 | 5.4% | 94.0% |

> A melhor politica adaptativa (**Thompson Sampling**) reduz o regret final em
> **97.6%** frente ao baseline fixo, convergindo para o braco otimo.

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
| UCB1 | imediato | 432.4 | 15.81% |
| UCB1 | atrasado | 514.1 | 15.42% |
| Thompson | imediato | 67.0 | 17.67% |
| Thompson | atrasado | 77.1 | 17.61% |

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
