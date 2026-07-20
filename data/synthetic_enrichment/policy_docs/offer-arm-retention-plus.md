# Politica do braco `arm_retention_plus` (sintetico)

**arm_id:** `arm_retention_plus` · **Nome:** Retencao consultiva plus

## Objetivo

Oferta de retencao sem incentivo financeiro agressivo. Alternativa quando
incentivos estao bloqueados ou o perfil exige abordagem consultiva.

## Quando e selecionado

- Redirecionamento de `arm_rate_boost` quando `financial_incentive_blocked=true`
  (`INCENTIVE_BLOCKED_REDIRECT`).
- Segmentos com historico positivo em canais telefonicos (golden set GS-S01).
- Perfis maduros com `poutcome=success` e macro `neutral`.

## Suitability

Preferido para clientes com relacionamento estabelecido que nao devem receber
taxas promocionais adicionais. Alinha com principio de minimizacao de incentivo.

## Comparacao com outros bracos

| Braco | Incentivo financeiro | Exploracao |
| --- | --- | --- |
| `arm_rate_boost` | Alto | Alta em celular |
| `arm_retention_plus` | Baixo | Moderada |
| `arm_control` | Nenhum | Fallback |
