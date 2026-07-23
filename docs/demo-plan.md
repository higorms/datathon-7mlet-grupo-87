# Plano de Demonstração — Datathon 7MLET (Grupo 87)

> **Etapa 8** · Cenário de demo ao vivo/gravada com plano de contingência.
> Roteiro do pitch: [`docs/pitch/roteiro.md`](pitch/roteiro.md).

## 1. Objetivo da demo

Demonstrar que a banca consegue:

1. Executar uma decisão de exemplo via API (`POST /decide`).
2. Ver o braço selecionado, a justificativa (`reason_codes`) e a versão da política.
3. Recuperar o registro auditável (`GET /audit/{decision_id}`).
4. Validar guardrails de segurança com casos adversariais do golden set.

## 2. Pré-requisitos

```bash
# Instalar dependências
poetry install

# Garantir dados processados (se necessário)
poetry run python -m src.data.prepare

# Subir a API
poetry run uvicorn src.service.app:app --host 127.0.0.1 --port 8000
```

Verificar saúde: `curl http://127.0.0.1:8000/health`

## 3. Cenários de demo (baseados no golden set)

### Cenário 1 — Caso típico: jovem com celular e sucesso (GS-T01)

**Narrativa:** "Cliente jovem (22 anos), canal celular, histórico de sucesso em macro tight.
A política seleciona taxa bonificada — maior score contextual."

```bash
curl -s -X POST http://127.0.0.1:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "age": 22,
    "contact": "cellular",
    "poutcome": "success",
    "pdays": 180,
    "previous": 2,
    "job": "student",
    "month": "oct",
    "segment_macro_regime": "tight",
    "segment_age_band": "17-25",
    "segment_history": "warm_history"
  }' | python -m json.tool
```

**Resultado esperado:**

```json
{
  "arm_id": "arm_rate_boost",
  "reason_codes": ["GREEDY_CONTEXT_MATCH"],
  "policy_version": "context-greedy-v1"
}
```

### Cenário 2 — Caso adversarial: alto risco (GS-A03)

**Narrativa:** "Jovem em cold-start com macro stress — trilho de segurança aciona fallback
para mensagem neutra de controle."

```bash
curl -s -X POST http://127.0.0.1:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "age": 23,
    "contact": "cellular",
    "poutcome": "unknown",
    "pdays": 999,
    "previous": 0,
    "job": "student",
    "month": "may",
    "segment_macro_regime": "stress",
    "segment_history": "cold_start"
  }' | python -m json.tool
```

**Resultado esperado:**

```json
{
  "arm_id": "arm_control",
  "reason_codes": ["SAFE_FALLBACK_HIGH_RISK"],
  "policy_version": "context-greedy-v1"
}
```

### Cenário 3 — Caso suitability: incentivo bloqueado (GS-A04)

**Narrativa:** "Cliente não elegível a incentivo financeiro — redirecionamento para oferta
de relacionamento alternativa."

```bash
curl -s -X POST http://127.0.0.1:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "contact": "cellular",
    "poutcome": "success",
    "pdays": 180,
    "previous": 2,
    "job": "management",
    "month": "oct",
    "segment_macro_regime": "tight",
    "financial_incentive_blocked": true
  }' | python -m json.tool
```

**Resultado esperado:**

```json
{
  "arm_id": "arm_retention_plus",
  "reason_codes": ["INCENTIVE_BLOCKED_REDIRECT"],
  "policy_version": "context-greedy-v1"
}
```

### Cenário 4 — Auditoria da decisão

Após qualquer cenário, copiar o `decision_id` da resposta e consultar:

```bash
curl -s http://127.0.0.1:8000/audit/{decision_id} | python -m json.tool
```

Mostrar que o registro contém contexto completo, reason codes e `policy_version`.

### Cenário 5 (opcional) — Ciclo MLOps

```bash
poetry run python -m src.mlops --candidate context-greedy-v2-rc --approve --demo-rollback
```

Demonstra approval gate, promoção e rollback em ~30 segundos.

## 4. Alternativa: pipeline ponta a ponta

Se preferir um único comando em vez da API interativa:

```bash
poetry run python scripts/run_pipeline.py
```

Executa Etapas 1 → 2 → 4 (golden set) → 5 (decisão auditável) e imprime o resultado.

## 5. Plano de contingência

### Falha 1: API não sobe (porta ocupada, dependência faltando)

**Ação:** usar Docker pré-buildado.

```bash
docker build -t datathon-decision-api .
docker run -p 8000:8000 datathon-decision-api
# Repetir cenários 1–3 com curl
```

### Falha 2: Rede indisponível no Demo Day

**Ação:** executar tudo localmente (sem dependência de internet). Dados e código estão no
repositório; `poetry install` + `uvicorn` funciona offline após instalação inicial.

### Falha 3: Demo ao vivo falha completamente

**Ação:** apresentar gravação de tela pré-gravada.

1. Gravar os 3 cenários acima com `asciinema` ou gravador de tela.
2. Versionar em `docs/pitch/demo-recording.md` com link e hash SHA-256 do arquivo.
3. Incluir no pitch: "Demo gravada por contingência — cenário e resultados documentados."

**Template para link de gravação** (`docs/pitch/demo-recording.md`):

```markdown
# Gravação de Demo — Contingência

- **Data:** YYYY-MM-DD
- **Duração:** ~3 min
- **Arquivo:** `demo-recording.mp4` (ou link externo)
- **SHA-256:** `abc123...`
- **Cenários cobertos:** GS-T01, GS-A03, GS-A04 + auditoria
```

### Falha 4: Pergunta técnica sobre métricas

**Ação:** apontar para relatórios versionados no repositório:

- `reports/offline-evaluation.md` (métricas e golden set)
- `reports/bandit-comparison.md` (comparação bandit)
- `docs/model-card.md` (governança)

## 6. Artefatos a versionar pós-demo

| Artefato | Local | Versionado? |
| --- | --- | --- |
| Log de exemplo da sessão | `docs/pitch/demo-session-log.jsonl` | Sim (sintético, sem PII) |
| Link/hash da gravação | `docs/pitch/demo-recording.md` | Sim |
| Slides PDF | `docs/pitch/slides.pdf` | Sim (gerado localmente) |

### Gerar log de exemplo para versionar

Após executar os 3 cenários, copiar as linhas relevantes de `logs/decisions.jsonl` para
`docs/pitch/demo-session-log.jsonl` (anonimizado — já é sintético por design).

## 7. Checklist pré-demo

- [ ] `poetry run pytest -q` — todos os testes passam
- [ ] API responde em `/health`
- [ ] Cenário 1 (GS-T01) retorna `arm_rate_boost`
- [ ] Cenário 2 (GS-A03) retorna `arm_control`
- [ ] Cenário 3 (GS-A04) retorna `arm_retention_plus`
- [ ] `GET /audit/{id}` retorna registro completo
- [ ] Docker image builda sem erro (contingência)
- [ ] Gravação de backup pronta (se aplicável)
- [ ] Slides exportados para PDF

## Referências

- Golden set: [`data/golden_set/evaluation_cases.jsonl`](../data/golden_set/evaluation_cases.jsonl)
- API: [`src/service/app.py`](../src/service/app.py)
- Roteiro do pitch: [`docs/pitch/roteiro.md`](pitch/roteiro.md)
- Pipeline: [`scripts/run_pipeline.py`](../scripts/run_pipeline.py)
