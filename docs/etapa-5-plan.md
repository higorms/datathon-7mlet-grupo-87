# Plano — Etapa 5: Serviço/API demonstrável

> Objetivo (enunciado): **expor a decisão de forma controlada e auditável.** A banca deve
> conseguir executar uma decisão de exemplo e ver: **braço selecionado, justificativa
> (reason codes), versão da política e o registro auditável gerado.**

## 1. Requisitos da etapa → como atender

| Requisito do enunciado | Como vamos entregar |
| --- | --- |
| API/CLI/notebook/app que recebe contexto e devolve decisão | **FastAPI** (`POST /decide`) + **CLI** one-shot (`python -m src.service.cli`) |
| Contrato de entrada/saída documentado, com exemplo e tratamento de erro | Modelos **Pydantic** (request/response) + `/docs` (OpenAPI) + exemplos no README |
| Log auditável com reason codes, braço e versão da política | Registro **JSONL** append-only por decisão (`decision_id`, timestamp, contexto, braço, reason codes, `policy_version`) |
| Comando único que reproduz o pipeline ponta a ponta local | Script `scripts/run_pipeline.py` (dados → sintético → avaliação → sobe serviço) |
| Suíte mínima de testes (contratos de dados, política, registro) | `tests/test_service.py` (contrato, safety rails, auditoria, erros) |

**Evidência de aceite:** `curl`/CLI de exemplo retorna braço + justificativa + versão +
`decision_id`, e o registro correspondente aparece no log auditável.

## 2. Arquitetura proposta

Reaproveitamos a **política contextual da Etapa 4** (`src/evaluation/context_policy.py`)
como núcleo de decisão — o serviço é uma casca fina, auditável, em volta dela.

```
src/service/
├── __init__.py
├── contracts.py      # Pydantic: DecisionRequest (entrada) e DecisionResponse (saída)
├── decision.py       # orquestra: valida -> decide_arm -> reason codes -> monta resposta
├── reason_codes.py   # enum/constantes de reason codes + mapeamento a partir da política
├── audit.py          # escreve/le o log auditável (JSONL append-only)
├── policy_meta.py    # POLICY_VERSION + hash do catálogo (rastreabilidade)
├── app.py            # FastAPI: POST /decide, GET /health, GET /audit/{decision_id}
└── cli.py            # decisão one-shot por linha de comando (sem subir servidor)
scripts/
└── run_pipeline.py   # comando único ponta a ponta (dados -> avaliação -> serviço)
tests/
└── test_service.py   # contrato, política, auditoria, tratamento de erro
```

Novas dependências (pyproject): `fastapi`, `uvicorn[standard]`, `httpx` (TestClient, dev).

## 3. Contrato de entrada (DecisionRequest)

| Campo | Tipo | Default | Observação |
| --- | --- | --- | --- |
| `age` | int (18–100) | — | obrigatório |
| `contact` | str | — | `cellular`/`telephone`; outro → safety rail |
| `poutcome` | str | `unknown` | histórico da campanha anterior |
| `pdays` | int | 999 | 999 = nunca contatado (sentinela) |
| `previous` | int | 0 | contatos anteriores |
| `job` | str | `unknown` | profissão |
| `month` | str | `may` | mês do contato |
| `segment_macro_regime` | str | `neutral` | `stress`/`neutral`/`tight` |
| `segment_history` | str? | — | `cold_start`/`warm_history` |
| `segment_age_band` | str? | — | faixa etária |
| `financial_incentive_blocked` | bool | false | bloqueia `arm_rate_boost` |
| `force_safe_fallback` | bool | false | força `arm_control` |

Validação por Pydantic → entrada inválida retorna **HTTP 422** com mensagem clara.

**Exemplo de request:**
```json
{ "age": 22, "contact": "cellular", "poutcome": "success", "pdays": 180,
  "job": "student", "month": "oct", "segment_macro_regime": "tight" }
```

## 4. Contrato de saída (DecisionResponse)

```json
{
  "decision_id": "b3f1…",
  "timestamp": "2026-07-10T13:00:00Z",
  "arm_id": "arm_rate_boost",
  "arm_name": "Taxa bonificada",
  "reason_codes": ["GREEDY_CONTEXT_MATCH"],
  "context_score": 0.91,
  "selection_probabilities": { "arm_control": 0.05, "arm_rate_boost": 0.62, "…": 0.0 },
  "policy_version": "context-greedy-v1",
  "catalog_hash": "74adfc…"
}
```

## 5. Reason codes (justificativa auditável)

| Código | Quando |
| --- | --- |
| `GREEDY_CONTEXT_MATCH` | decisão normal pela política gulosa contextual |
| `SAFE_FALLBACK_INVALID_CHANNEL` | canal fora de {cellular, telephone} → `arm_control` |
| `SAFE_FALLBACK_FORCED` | flag `force_safe_fallback` → `arm_control` |
| `SAFE_FALLBACK_HIGH_RISK` | jovem + cold-start + macro stress → `arm_control` |
| `INCENTIVE_BLOCKED_REDIRECT` | incentivo bloqueado e guloso seria `arm_rate_boost` → `arm_retention_plus` |

Os códigos derivam **exatamente** dos trilhos de segurança já implementados em
`context_policy.py` — o serviço só os torna explícitos na resposta e no log.

## 6. Log auditável

- Formato: **JSONL append-only** em `logs/decisions.jsonl` (não versionado — runtime).
- Cada linha = a `DecisionResponse` + o `context` de entrada, permitindo reconstruir a decisão.
- Endpoint `GET /audit/{decision_id}` para recuperar um registro (demonstra a auditoria).
- `.gitignore`: adicionar `logs/` (dados de execução não vão para o repo).

## 7. Endpoints

| Método | Rota | Função |
| --- | --- | --- |
| `POST` | `/decide` | recebe contexto, retorna decisão + grava auditoria |
| `GET` | `/health` | liveness/readiness (útil para Azure na Etapa 6) |
| `GET` | `/audit/{decision_id}` | recupera um registro auditável |
| `GET` | `/docs` | OpenAPI/Swagger (contrato interativo, automático) |

## 8. Comando único ponta a ponta

`scripts/run_pipeline.py` executa em sequência: (1) `src.data.prepare`, (2) checa/gera a
camada sintética, (3) `src.evaluation` (golden set + métricas) e (4) sobe o serviço
(`uvicorn`). Documentado no README. Alternativa sem servidor:
`python -m src.service.cli --context '{...}'` imprime a decisão + grava auditoria.

## 9. Testes mínimos (`tests/test_service.py`)

- **Contrato:** request válida → 200 com todos os campos; request inválida → 422.
- **Política/safety rails:** canal inválido → `arm_control` + `SAFE_FALLBACK_INVALID_CHANNEL`;
  incentivo bloqueado → nunca `arm_rate_boost`; caso típico → braço esperado + reason code.
- **Auditoria:** uma decisão grava um registro recuperável com todos os campos exigidos
  (decision_id, reason codes, policy_version).
- **Versão da política:** presente e estável na resposta.

Usar `fastapi.testclient.TestClient` (sem subir servidor real).

## 10. Ganchos para as próximas etapas

- **Etapa 6 (Azure):** `/health` para probes; serviço containerizável (App Service /
  Container Apps); `catalog_hash`/`policy_version` para rastreio.
- **Etapa 7 (MLOps):** `policy_version` habilita promoção/rollback de políticas; o log
  auditável alimenta monitoramento de drift/recompensa.

## 11. Checklist de aceite da Etapa 5

- [ ] `POST /decide` recebe contexto e devolve braço + reason codes + versão + `decision_id`
- [ ] Contrato de entrada/saída documentado (Pydantic + `/docs`) com exemplo e erro 422
- [ ] Log auditável JSONL com reason codes, braço e `policy_version`
- [ ] `GET /audit/{decision_id}` recupera o registro
- [ ] CLI one-shot e script de pipeline ponta a ponta
- [ ] `tests/test_service.py` cobrindo contrato, política e auditoria (verde)
- [ ] README atualizado (como subir o serviço, exemplo de chamada, tratamento de erro)
- [ ] `.gitignore` ignora `logs/`; ruff limpo
