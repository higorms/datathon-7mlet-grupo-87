# Politica do braco `arm_rate_boost` (sintetico)

**arm_id:** `arm_rate_boost` · **Nome:** Taxa bonificada

## Objetivo

Oferta com incentivo financeiro sintetico para clientes com alta propensao
(contexto celular, historico positivo, segmentos jovens em regime `tight`).

## Elegibilidade

| Requisito | Valor |
| --- | --- |
| Canal | `cellular` ou `telephone` |
| Bloqueio | `financial_incentive_blocked` deve ser `false` |
| Suitability | Sem flags de fallback ativas |

## Restricoes

Se `financial_incentive_blocked=true`, a politica **nao** pode selecionar este braco.
O servico redireciona para `arm_retention_plus` com reason code
`INCENTIVE_BLOCKED_REDIRECT`.

## Riscos operacionais

- Super-exposicao em segmentos jovens (fairness Etapa 4).
- Sensibilidade a canal: celular infla sistematicamente a selecao deste braco.
- Recompensa atrasada (horizonte 14 dias) — decisao de serving nao deve assumir
  conversao imediata.

## Reason code

`GREEDY_CONTEXT_MATCH` quando selecionado pela politica gulosa contextual.
