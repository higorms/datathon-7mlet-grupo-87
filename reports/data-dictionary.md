# Dicionário de Dados — Bank Marketing

Descrição das **21 colunas originais** de `bank-additional-full.csv` e o que acontece
com cada uma no **dataset processado** (`data/processed/bank_marketing.parquet`).

Legenda da coluna *Status no processado*:
- **feature** — mantida como variável de contexto para a decisão.
- **alvo** — variável-resposta (recompensa proxy).
- **descartada (vazamento)** — removida por vazamento pós-contato.
- **renomeada** — mantida, com nome ajustado (ponto → underscore).

## Dados do cliente

| # | Coluna original | Tipo | Descrição | Status no processado |
| --- | --- | --- | --- | --- |
| 1 | `age` | numérica | Idade do cliente (17–98). | feature |
| 2 | `job` | categórica | Profissão (12 categorias: `admin.`, `blue-collar`, `technician`, ..., `unknown`). | feature |
| 3 | `marital` | categórica | Estado civil (`married`, `single`, `divorced`*, `unknown`). *inclui viúvo(a). | feature |
| 4 | `education` | categórica | Escolaridade (8 categorias, ex.: `university.degree`, `high.school`, `basic.9y`, `unknown`). | feature |
| 5 | `default` | categórica | Possui crédito em inadimplência? (`no`, `yes`, `unknown`). ~21% `unknown`. | feature |
| 6 | `housing` | categórica | Possui financiamento imobiliário? (`no`, `yes`, `unknown`). | feature |
| 7 | `loan` | categórica | Possui empréstimo pessoal? (`no`, `yes`, `unknown`). | feature |

## Último contato da campanha atual

| # | Coluna original | Tipo | Descrição | Status no processado |
| --- | --- | --- | --- | --- |
| 8 | `contact` | categórica | Canal do contato (`cellular`, `telephone`). | feature |
| 9 | `month` | categórica | Mês do último contato (`mar`…`dec`; sem jan/fev na base). | feature |
| 10 | `day_of_week` | categórica | Dia da semana do último contato (`mon`–`fri`). | feature |
| 11 | `duration` | numérica | **Duração em segundos do último contato.** Só conhecida após a ligação. | **descartada (vazamento)** |

## Outros atributos

| # | Coluna original | Tipo | Descrição | Status no processado |
| --- | --- | --- | --- | --- |
| 12 | `campaign` | numérica | Nº de contatos nesta campanha para o cliente (inclui o último). | feature |
| 13 | `pdays` | numérica | Dias desde o último contato de campanha anterior. **`999` = nunca contatado** (~96%). | feature (sentinela documentado) |
| 14 | `previous` | numérica | Nº de contatos antes desta campanha. | feature |
| 15 | `poutcome` | categórica | Resultado da campanha **anterior** (`success`, `failure`, `nonexistent`). | feature |

## Contexto socioeconômico (indicadores macro)

| # | Coluna original | Tipo | Descrição | Status no processado |
| --- | --- | --- | --- | --- |
| 16 | `emp.var.rate` | numérica | Taxa de variação do emprego (trimestral). | renomeada → `emp_var_rate` |
| 17 | `cons.price.idx` | numérica | Índice de preços ao consumidor (mensal). | renomeada → `cons_price_idx` |
| 18 | `cons.conf.idx` | numérica | Índice de confiança do consumidor (mensal). | renomeada → `cons_conf_idx` |
| 19 | `euribor3m` | numérica | Taxa Euribor 3 meses (diária). | feature |
| 20 | `nr.employed` | numérica | Número de empregados (trimestral). | renomeada → `nr_employed` |

## Variável-alvo

| # | Coluna original | Tipo | Descrição | Status no processado |
| --- | --- | --- | --- | --- |
| 21 | `y` | binária | Cliente assinou o depósito a prazo? (`yes`/`no`). | **alvo** → `subscribed` (1/0); `y` textual descartado |

## Observações de uso

- **Tipagem no processado:** categóricas viram `category`; numéricas usam tipos
  compactos (`int8`/`int16`/`float64`) — ver `df.dtypes`.
- **`unknown` ≠ NaN:** o `unknown` é uma categoria explícita de ausência; não há
  células vazias no CSV. Quantificado em `reports/data-quality.md` (seção 4).
- **`pdays == 999`:** tratar como sentinela ("nunca contatado"), não como valor
  contínuo — relevante para qualquer modelo sensível a escala.
- **Papel no bandit (próximas etapas):** as *features* acima formam o **contexto** da
  decisão; `subscribed` será a base da **recompensa**. As **ofertas/braços** virão da
  camada sintética da Etapa 2, não desta base.
