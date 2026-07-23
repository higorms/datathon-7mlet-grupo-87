# Relatório Técnico — Datathon 7MLET (Grupo 87)

> Plataforma de experimentação adaptativa (multi-armed bandit) para ofertas em canais digitais.
> **Grupo 87** · Higor Menezes · Narcélio Sousa · Julho 2026

---

## 1. Problema e motivação

Instituições financeiras digitais precisam decidir, em diferentes canais, qual oferta, mensagem
ou próximo passo apresentar a cada cliente elegível. Regras fixas e testes A/B longos desperdiçam
tráfego, demoram a reagir a mudanças de contexto e dificultam a personalização responsável.

Uma abordagem de **multi-armed bandit** equilibra exploração e explotação, aprendendo com respostas
observadas sem congelar a decisão em regras estáticas. O objetivo deste projeto não é reproduzir um
sistema bancário real, mas demonstrar **maturidade de Machine Learning Engineering** ponta a ponta:
formular o problema, versionar dados, servir a decisão, avaliar qualidade, monitorar risco e
governar o ciclo de vida.

## 2. Base de dados escolhida (Etapa 1)

### 2.1 Fonte

| Campo | Valor |
| --- | --- |
| Dataset | Bank Marketing (`bank-additional-full.csv`) |
| Kaggle | [henriqueyamahata/bank-marketing](https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing) |
| UCI (canônica) | [Dataset 222](https://archive.ics.uci.edu/dataset/222/bank+marketing) |
| Licença | CC BY 4.0 |
| Registros | 41.188 linhas × 21 colunas |

**Justificativa:** campanhas de telemarketing bancário com target `y` (assinou depósito a prazo) como
proxy de conversão; rica em contexto macroeconômico; vazamento documentável (`duration`).

### 2.2 Tratamento de vazamento

A coluna `duration` (duração da ligação, conhecida só após o contato) foi **descartada** por ser
quase perfeitamente correlacionada com o target — vazamento pós-contato clássico. Decisão documentada
em [`reports/data-quality.md`](data-quality.md) com evidência quantitativa.

### 2.3 Pipeline reprodutível

```bash
poetry run python -m src.data.prepare
```

Gera `data/processed/bank_marketing.parquet` (sem vazamento) + `metadata.json` com SHA-256,
fonte, versão e licença. EDA em [`notebooks/01_eda.ipynb`](../notebooks/01_eda.ipynb).

## 3. Enriquecimento sintético (Etapa 2)

Sobre a base processada, criamos uma camada de experimentação adaptativa em
`data/synthetic_enrichment/`:

| Artefato | Conteúdo |
| --- | --- |
| `offer_catalog.parquet` | 5 braços/ofertas com `base_score` |
| `offer_events.parquet` | Impressões, contexto de decisão, atribuição de braços |
| `delayed_rewards.parquet` | Recompensas intermediárias e atrasadas (horizonte 14 dias) |
| `policy_docs/` | Corpus sintético para RAG (suitability, elegibilidade) |

**Sementes controladas:** catálogo `20240622`, política `20240623`, recompensas `20240624`.
Processo documentado em [`reports/data-generation.md`](data-generation.md).

**Braços:**

| arm_id | Nome | true_p (simulação) |
| --- | --- | --- |
| `arm_rate_boost` | Taxa bonificada | 0.180 (ótimo) |
| `arm_consultative_call` | Contato consultivo | 0.145 |
| `arm_digital_bundle` | Pacote digital | 0.110 |
| `arm_retention_plus` | Oferta de relacionamento | 0.075 |
| `arm_control` | Mensagem neutra | 0.040 |

## 4. Modelagem como multi-armed bandit (Etapas 3–4)

### 4.1 Algoritmos comparados

| Algoritmo | Papel | Implementação |
| --- | --- | --- |
| Baseline fixo | Controle determinístico (sempre `arm_control`) | `src/bandits/policies.py` |
| Epsilon-greedy (ε=0.1) | Baseline adaptativo simples | `src/bandits/policies.py` |
| UCB1 (Nilos-UCB) | Exploração por otimismo sob incerteza | `src/bandits/policies.py` |
| Thompson Sampling | Exploração bayesiana (prior Beta(1,1)) | `src/bandits/policies.py` |

### 4.2 Resultados quantitativos

Configuração: horizonte 10.000, 15 sementes ([`reports/offline-evaluation.md`](offline-evaluation.md)).

| Política | Conversão | Regret final | % braço ótimo |
| --- | --- | --- | --- |
| Baseline fixo | 4.03% | 1400.0 | 0.0% |
| Epsilon-greedy | 16.45% | 147.7 | 70.1% |
| UCB1 (Nilos-UCB) | 15.14% | 293.9 | 55.0% |
| **Thompson Sampling** | **17.38%** | **56.6** | **90.2%** |

Thompson Sampling reduz o regret em **96%** frente ao baseline fixo, convergindo para o braço ótimo
com apenas 9% de exploração. UCB1 explora mais (44.6%) com regret intermediário — trade-off
confiança/exploração documentado na análise de sensibilidade (`ucb_c` de 0.5 a 2.0).

### 4.3 Cold-start e delayed rewards

- **Cold-start:** Thompson Sampling usa prior Beta(1,1) para exploração natural; UCB1 joga cada
  braço uma vez. Ambos eficazes; política servida usa trilhos de segurança para perfis de alto risco.
- **Delayed rewards:** regret aumenta de 56.6 (imediato) para ~77 (atrasado médio 500 rodadas).
  Modelado em `delayed_rewards.parquet` com censura por horizonte de 14 dias.

### 4.4 Política servida vs. simulação

| Camada | Política | Papel |
| --- | --- | --- |
| Simulação | Thompson Sampling | Melhor candidato adaptativo (menor regret) |
| Serving | `context-greedy-v1` | Gulosa contextual + guardrails auditáveis |

A política servida prioriza **auditabilidade e segurança** sobre exploração estocástica.

### 4.5 Golden set e avaliação offline

24 casos versionados em `data/golden_set/evaluation_cases.jsonl` (typical, edge, segment,
adversarial). **Pass rate: 100%** (24/24). Fairness de exposição calculada por segmento
(max/min ratio ≤ 1.26 em `segment_age_band`).

## 5. Serviço demonstrável (Etapa 5)

API FastAPI com contrato documentado:

```bash
curl -X POST http://127.0.0.1:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"age": 22, "contact": "cellular", "poutcome": "success", "month": "oct"}'
```

Retorna `arm_id`, `reason_codes`, `policy_version`, `decision_id`. Log auditável em
`logs/decisions.jsonl`. Pipeline ponta a ponta: `poetry run python scripts/run_pipeline.py`.

## 6. Arquitetura-alvo Azure (Etapa 6)

Mapeamento local → Azure exclusivamente:

| Camada | Local | Azure |
| --- | --- | --- |
| Compute | FastAPI + uvicorn | Container Apps |
| API | `/decide`, `/audit/{id}` | API Management + Entra ID |
| Dados | parquet + JSONL | ADLS Gen2 + Azure SQL |
| IA/RAG | `policy_docs/` | Azure OpenAI + AI Search |
| Observabilidade | `logs/decisions.jsonl` | App Insights + Log Analytics |
| Segurança | `.env` local | Key Vault + Managed Identity |

**Decisão de compute:** Container Apps como primário (~$120–150/mês dev); AKS como evolução
de escala (>100k req/dia). Detalhes em [`docs/architecture-azure.md`](../docs/architecture-azure.md).

### FinOps (estimativa qualitativa)

| Serviço | Dev (USD/mês) | Prod 10k req/dia |
| --- | --- | --- |
| Container Apps | $15–30 | $80–150 |
| API Management | $5 | $50+ |
| AI Search Basic | $75 | $250+ |
| Azure OpenAI | $10 | $100+ |
| **TCO estimado** | **~$120–150** | **~$600–900** |

ROI narrativo: regret 1400 (baseline) → 56.6 (Thompson Sampling); golden set 100% pass rate.

## 7. Ciclo de vida MLOps (Etapa 7)

Fluxo: experimento → MLflow → approval gate → aprovação humana → promoção (dev → staging → prod)
→ monitoramento (PSI, reward_trend) → rollback se degradar.

Critérios do gate: `golden_pass_rate ≥ 1.0`, `regret ≤ 300`, `optimal_arm_rate ≥ 0.60`,
`fallback_rate ≤ 0.30`. Demonstrável via:

```bash
poetry run python -m src.mlops --candidate context-greedy-v2-rc --approve --demo-rollback
```

## 8. Governança (Etapa 8)

- **Model card:** [`docs/model-card.md`](../docs/model-card.md) — métricas, intended use, fairness, limitações.
- **System card:** [`docs/system-card.md`](../docs/system-card.md) — guardrails, 4 cenários de risco, monitoramento.
- **Plano LGPD:** [`docs/lgpd-plan.md`](../docs/lgpd-plan.md) — minimização, retenção, resposta a incidentes.

## 9. Limitações, riscos e hipóteses

### Limitações

- Base estática (Portugal 2008–2013); não generaliza sem retreino.
- Camada sintética não é causal; confundimento braço-desfecho no log original.
- Simulação bandit é não-contextual; serving é contextual — camadas complementares.
- Desbalanceamento forte (~11,7% conversão).

### Riscos operacionais

| Risco | Mitigação |
| --- | --- |
| Reward hacking | Approval gate + monitoramento PSI/recompensa |
| Manipulação de contexto | Validação Pydantic + SAFE_FALLBACK_* |
| Abuso do assistente RAG | Corpus sintético, citações obrigatórias, humano no loop |
| Violação de suitability | INCENTIVE_BLOCKED_REDIRECT + golden set adversarial |

### Hipóteses

- Thompson Sampling é superior a UCB1 e baseline fixo em regret e conversão (confirmada).
- Política contextual gulosa com guardrails atinge 100% no golden set (confirmada).
- Feedback atrasado degrada regret mensuravelmente (confirmada na sensibilidade).

## 10. Trabalhos futuros

1. **LinUCB contextual:** extensão natural do UCB com modelo linear do contexto.
2. **Endpoint `/explain`:** assistente RAG (Azure OpenAI + AI Search) para explicar decisões.
3. **Deploy Azure real:** Container Apps + Key Vault + Managed Identity.
4. **Retreino contínuo:** pipeline agendado com approval gate e canary deploy.
5. **Fairness constraints:** caps de exploração por segmento vulnerável.
6. **Integração com canal real:** webhook de recompensa atrasada para atualização online.

## Referências

1. Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI ML Repository. https://doi.org/10.24432/C5K306
2. Thompson, W. R. (1933). On the likelihood that one unknown probability exceeds another. *Biometrika*, 25(3/4), 285–294.
3. Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time analysis of the multiarmed bandit problem. *Machine Learning*, 47(2), 235–256.
4. Mitchell, M. et al. (2019). Model Cards for Model Reporting. *FAccT*.
5. Documentação do projeto: repositório `datathon-7mlet-grupo-87` (Etapas 0–8).

---

*Relatório gerado em Julho 2026. Reproduzível via comandos documentados no README.*
