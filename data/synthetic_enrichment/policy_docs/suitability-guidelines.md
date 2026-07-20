# Diretrizes de Suitability (sintetico)

**Versao:** `policy-synth-v1` · **Escopo:** experimentacao adaptativa em canais digitais

## Finalidade

Estabelecer criterios de adequacao para apresentacao de ofertas a clientes elegiveis,
sem uso de dados pessoais identificaveis. Decisoes automatizadas devem ser
auditaveis (`decision_id`, `reason_codes`, `policy_version`).

## Principios

1. **Minimizacao:** usar apenas contexto necessario (idade, canal, historico de campanha, segmento macro).
2. **Fallback seguro:** perfis de alto risco ou canal invalido recebem `arm_control` (oferta neutra).
3. **Incentivo financeiro:** `arm_rate_boost` exige canal `cellular` ou `telephone` e ausencia de bloqueio `financial_incentive_blocked`.
4. **Humano no loop:** excecoes regulatorias ou reclamacoes exigem revisao manual antes de nova impressao.

## Segmentos de contexto

| Segmento | Criterio sintetico | Observacao |
| --- | --- | --- |
| `cold_start` | `pdays >= 999` ou `previous == 0` | Maior incerteza; preferir exploracao controlada |
| `warm_history` | Contato previo documentado | Permite personalizacao com historico |
| `stress` / `tight` / `neutral` | Regime macro sintetico | Ajusta agressividade de incentivo |

## Proibicoes

- Nao usar genero, raca, renda ou patrimonio (ausentes na base).
- Nao prometer retorno financeiro garantido.
- Nao contatar por canais nao elegiveis (`email`, `unknown`).
