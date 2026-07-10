# Golden set — Etapa 4

Conjunto versionado de casos de avaliacao offline para a politica contextual antes do serving (Etapa 5).

## Arquivo

- [`evaluation_cases.jsonl`](evaluation_cases.jsonl) — **24 casos** (minimo exigido: 20), um JSON por linha.

## Schema (resumo)

| Campo | Descricao |
| --- | --- |
| `case_id` | Identificador estavel (`GS-T01`, `GS-E01`, …) |
| `category` | `typical`, `edge`, `segment` ou `adversarial` |
| `title` | Titulo legivel do cenario |
| `context` | Features de decisao (idade, canal, segmentos, flags de seguranca) |
| `expected_arm_id` | Braço esperado pela politica documentada |
| `expected_reward` | `min`, `max`, `true_p_ref` (taxa Bernoulli do ambiente Etapa 3) |
| `justification` | Motivo de negocio/tecnico do resultado esperado |
| `pass_criteria` | Criterio explicito de pass/fail |
| `tags` | Etiquetas para rastreio |

Contrato Pydantic completo: [`src/evaluation/schema.py`](../../src/evaluation/schema.py).

## Matriz de cobertura

| Categoria | Casos | Foco |
| --- | --- | --- |
| `typical` | 6 | Perfis comuns com sinal claro (jovem+celular, aposentado+telefone, …) |
| `edge` | 6 | Cold-start, unknown, off-peak, macro stress no limiar, faixa 66+ |
| `segment` | 6 | Combinacoes de `segment_macro_regime`, `segment_history`, `segment_age_band` |
| `adversarial` | 6 | Canal invalido, stress+jovem+cold-start, incentivo bloqueado, fallback forcado |

## Criterios de pass/fail

| `type` | Significado |
| --- | --- |
| `arm_equals` | Braço previsto deve ser exatamente `value` |
| `arm_in_set` | Braço previsto deve estar em `value` (lista) |
| `arm_not_equals` | Braço previsto nao pode ser `value` |
| `min_context_score` | Score do braço escolhido >= `value` |

## Politica avaliada

Os casos sao avaliados por `decide_arm()` em [`src/evaluation/context_policy.py`](../../src/evaluation/context_policy.py):

1. Trilhos de seguranca (canal invalido, perfil de alto risco, fallback forcado)
2. Politica gulosa contextual (mesmos pesos da Etapa 2)
3. Redirecionamento quando `financial_incentive_blocked` impede `arm_rate_boost`

## Como adicionar casos

1. Defina o contexto e calcule o braço com `poetry run python -c "from src.evaluation.context_policy import decide_arm; print(decide_arm({...}))"`.
2. Adicione uma linha JSON ao `evaluation_cases.jsonl`.
3. Rode `poetry run python -m src.evaluation` e `poetry run pytest tests/test_evaluation.py`.

## Reproducao

```bash
poetry run python -m src.evaluation
```
