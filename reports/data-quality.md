# Relatorio de Qualidade de Dados - Etapa 1

> Gerado automaticamente por `src/data/quality.py` em 2026-06-19 18:49 UTC.
> Reproduza com: `poetry run python -m src.data.prepare`.

## 1. Proveniencia

| Campo | Valor |
| --- | --- |
| Base | Bank Marketing (bank-additional-full) |
| Kaggle | https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing |
| Fonte factual (UCI) | https://archive.ics.uci.edu/dataset/222/bank+marketing |
| Versao | UCI 2014-02-13 (Moro et al., 2014) |
| Licenca | CC BY 4.0 (UCI Machine Learning Repository) |
| Arquivo bruto | `bank-additional-full.csv` |
| SHA-256 (bruto) | `74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8` |

Citacao: Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5K306

## 2. Dimensoes

| Conjunto | Linhas | Colunas |
| --- | --- | --- |
| Bruto (raw) | 41188 | 21 |
| Processado (sem vazamento) | 39404 | 20 |

- Linhas exatamente duplicadas removidas: **1784**.
- Colunas removidas por vazamento: **duration**.

## 3. Distribuicao do alvo (`subscribed`)

| classe | contagem | percentual |
| --- | --- | --- |
| 0 (nao assinou) | 34806 | 88.33 |
| 1 (assinou) | 4598 | 11.67 |

> **Desbalanceamento de classe:** apenas **11.67%** dos casos sao conversoes
> (classe positiva). Isso exige metricas alem da acuracia (ex.: AUC-PR, recall, lift) e
> sera relevante para o tratamento de recompensas no bandit.

## 4. Valores ausentes

No CSV original nao ha celulas vazias, mas varias categoricas usam o token
`"unknown"` como ausencia disfarcada. Tabela por coluna:

| coluna | nan | unknown | ausentes_total | ausentes_% |
| --- | --- | --- | --- | --- |
| default | 0 | 8266 | 8266 | 20.98 |
| education | 0 | 1686 | 1686 | 4.28 |
| housing | 0 | 980 | 980 | 2.49 |
| loan | 0 | 980 | 980 | 2.49 |
| job | 0 | 325 | 325 | 0.82 |
| marital | 0 | 79 | 79 | 0.2 |
| age | 0 | 0 | 0 | 0.0 |
| contact | 0 | 0 | 0 | 0.0 |
| month | 0 | 0 | 0 | 0.0 |
| day_of_week | 0 | 0 | 0 | 0.0 |
| campaign | 0 | 0 | 0 | 0.0 |
| pdays | 0 | 0 | 0 | 0.0 |
| previous | 0 | 0 | 0 | 0.0 |
| poutcome | 0 | 0 | 0 | 0.0 |
| emp_var_rate | 0 | 0 | 0 | 0.0 |
| cons_price_idx | 0 | 0 | 0 | 0.0 |
| cons_conf_idx | 0 | 0 | 0 | 0.0 |
| euribor3m | 0 | 0 | 0 | 0.0 |
| nr_employed | 0 | 0 | 0 | 0.0 |
| subscribed | 0 | 0 | 0 | 0.0 |

> Decisao Etapa 1: **nao imputar** ainda. Documentamos a ausencia e mantemos
> `unknown` como categoria propria; a estrategia de imputacao fica para a modelagem.

## 5. Resumo numerico

| coluna | n | media | desvio | min | q25 | mediana | q75 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age | 39404.0 | 40.116 | 10.46 | 17.0 | 32.0 | 38.0 | 47.0 | 98.0 |
| campaign | 39404.0 | 2.619 | 2.815 | 1.0 | 1.0 | 2.0 | 3.0 | 56.0 |
| pdays | 39404.0 | 960.847 | 190.869 | 0.0 | 999.0 | 999.0 | 999.0 | 999.0 |
| previous | 39404.0 | 0.179 | 0.503 | 0.0 | 0.0 | 0.0 | 0.0 | 7.0 |
| emp_var_rate | 39404.0 | 0.064 | 1.577 | -3.4 | -1.8 | 1.1 | 1.4 | 1.4 |
| cons_price_idx | 39404.0 | 93.578 | 0.584 | 92.201 | 93.075 | 93.798 | 93.994 | 94.767 |
| cons_conf_idx | 39404.0 | -40.5 | 4.644 | -50.8 | -42.7 | -41.8 | -36.4 | -26.9 |
| euribor3m | 39404.0 | 3.601 | 1.742 | 0.634 | 1.334 | 4.857 | 4.961 | 5.045 |
| nr_employed | 39404.0 | 5165.986 | 72.764 | 4963.6 | 5099.1 | 5191.0 | 5228.1 | 5228.1 |

- `pdays == 999` (cliente nunca contatado antes): **37890**
  linhas (96.16%). E um **sentinela**, nao um valor continuo.

## 6. Resumo categorico

| coluna | n_categorias | top | top_freq_% |
| --- | --- | --- | --- |
| job | 12 | admin. | 25.06 |
| marital | 4 | married | 60.58 |
| education | 8 | university.degree | 29.34 |
| default | 3 | no | 79.01 |
| housing | 3 | yes | 52.18 |
| loan | 3 | no | 81.84 |
| contact | 2 | cellular | 62.62 |
| month | 10 | may | 33.79 |
| day_of_week | 5 | thu | 20.8 |
| poutcome | 3 | nonexistent | 85.93 |

## 7. Evidencia de vazamento - `duration`

Por que `duration` foi **descartada** (decisao da Etapa 1):

| Evidencia | Valor |
| --- | --- |
| Correlacao ponto-bisserial duration x alvo | **0.4053** |
| Duracao media - assinou | 553.2 s |
| Duracao media - nao assinou | 220.8 s |
| Casos com `duration == 0` | 4 |
| Fracao 'no' quando `duration == 0` | 1.0 |

> A `duration` so e conhecida **depois** da ligacao - quando o desfecho ja ocorreu.
> A forte correlacao e o padrao `duration==0 => 'no'` confirmam vazamento pos-contato.
> Mante-la inflaria artificialmente qualquer metrica. **Coluna removida do dataset de decisao.**

## 8. Conclusao

- Origem, versao e licenca rastreaveis (secao 1) e fixadas por hash.
- Dataset de decisao **sem vazamento pos-contato** (secao 7).
- Principais riscos para as proximas etapas: **forte desbalanceamento** (secao 3) e
  **ausencia disfarcada de `unknown`** em colunas socioeconomicas (secao 4).
