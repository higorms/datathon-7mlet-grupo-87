# Enriquecimento sintetico - Etapa 2

Esta pasta guarda a camada sinteticamente enriquecida usada para a experimentacao adaptativa.
Ela fica **fisicamente separada** da base Kaggle original em `data/kaggle/raw/` e consome apenas
`data/processed/bank_marketing.parquet` como ponto de partida.

Notebook gerador: [`notebooks/02_enriquecimento_sintetico.ipynb`](../../notebooks/02_enriquecimento_sintetico.ipynb)

## Objetivo

Criar um catalogo sintetico de bracos/ofertas e os logs de decisao necessarios para simular
um bandit contextual com recompensas intermediarias e recompensas atrasadas.

## Sementes e horizonte

- Sementes controladas: catalogo, politica e recompensas sao gerados de forma deterministica no notebook.
- Horizonte temporal padrao: `14` dias.
- Recompensa final: proxy de conversao baseado em `subscribed`.
- Recompensa intermediaria: sinal de engajamento de curto prazo, separado da recompensa final.
- Censura: eventos positivos que ultrapassam o horizonte sao marcados como `censored`.

## Arquivos gerados

### `offer_catalog.parquet`
Catalogo estatico dos bracos/ofertas.

| Coluna | Tipo | Descricao |
| --- | --- | --- |
| `arm_id` | string | Identificador sintetico do braco. |
| `arm_name` | string | Nome legivel da oferta. |
| `channel` | string | Canal sintetico associado ao braco. |
| `objective` | string | Objetivo de negocio da oferta. |
| `value_proposition` | string | Resumo da proposta de valor. |
| `target_segment` | string | Segmento de contexto mais provavel de aderencia. |
| `base_score` | float | Peso base da politica. |
| `delay_mean_days` | float | Media da distribuicao de atraso da recompensa. |
| `delay_std_days` | float | Desvio da distribuicao de atraso da recompensa. |
| `horizon_days` | int | Horizonte maximo de observacao da recompensa. |
| `notes` | string | Observacao curta sobre o papel do braco. |
| `generated_with_seed` | int | Semente usada para gerar o catalogo de forma reprodutivel. |

### `offer_events.parquet`
Log de impressao e decisao.

| Coluna | Tipo | Descricao |
| --- | --- | --- |
| `impression_id` | int | Identificador unico da impressao. |
| `customer_id` | int | Linha de origem do dataset processado. |
| `decision_ts` | datetime | Timestamp sintetico da decisao. |
| `arm_id` | string | Braco escolhido. |
| `arm_name` | string | Nome legivel do braco. |
| `channel` | string | Canal atribuido ao braco. |
| `objective` | string | Objetivo da oferta. |
| `selection_probability` | float | Probabilidade da politica para o braco escolhido. |
| `exploration_flag` | bool | Indica se a escolha saiu do argmax da politica. |
| `context_score` | float | Score contextual do braco escolhido. |
| `segment_age_band` | string | Faixa etaria sintetica. |
| `segment_history` | string | `cold_start` ou `warm_history`. |
| `segment_macro_regime` | string | Regime macro sintetico (`stress`, `neutral`, `tight`). |
| `poutcome` | string | Sinal historico mantido no contexto. |
| `contact` | string | Canal historico mantido no contexto. |
| `job` | string | Profissao mantida no contexto. |
| `subscribed` | int | Proxy historico do desfecho, preservado para calibrar o mundo sintetico. |
| `intermediate_reward_probability` | float | Probabilidade da recompensa intermediaria. |
| `intermediate_reward` | int | Sinal de engajamento de curto prazo. |
| `intermediate_reward_delay_days` | float | Atraso sintetico da recompensa intermediaria. |
| `reward_horizon_days` | int | Horizonte de observacao usado na simulacao. |

### `delayed_rewards.parquet`
Log da recompensa final atrasada.

| Coluna | Tipo | Descricao |
| --- | --- | --- |
| `impression_id` | int | Chave da impressao correspondente. |
| `customer_id` | int | Linha de origem do dataset processado. |
| `decision_ts` | datetime | Timestamp sintetico da decisao. |
| `arm_id` | string | Braco que recebeu a impressao. |
| `arm_name` | string | Nome legivel do braco. |
| `reward_value` | int | Recompensa final observada (`0`/`1`). |
| `reward_delay_days` | float | Dias entre decisao e observacao da recompensa. |
| `reward_observed_at` | datetime | Timestamp sintetico da observacao. |
| `within_horizon` | bool | Se a recompensa foi observada dentro do horizonte. |
| `reward_status` | string | `observed`, `censored` ou `no_conversion`. |
| `horizon_days` | int | Horizonte maximo de observacao. |

## Processo de geracao

1. Carregar o dataset processado em `data/processed/`.
2. Derivar segmentos de contexto sem usar a base Kaggle bruta.
3. Montar o catalogo sintetico de bracos/ofertas.
4. Simular uma politica estocastica controlada por sementes.
5. Gerar recompensas intermediarias e recompensas finais atrasadas.
6. Persistir os artefatos em `data/synthetic_enrichment/`.

## Documentos de politica (RAG — Etapa 6)

Politicas sinteticas em [`policy_docs/`](policy_docs/) para o assistente com LLM
(Azure OpenAI + AI Search). Ver [`policy_docs/README.md`](policy_docs/README.md).

## Observacoes

- Nao ha copia do CSV bruto do Kaggle nesta pasta.
- O horizonte de 14 dias documenta a janela maxima para observar a recompensa final.
- O objetivo e descrever a camada de experimentacao, nao treinar um modelo de producao.
