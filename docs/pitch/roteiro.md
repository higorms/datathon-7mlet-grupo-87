# Roteiro do Pitch — Datathon 7MLET (Grupo 87)

> **Duração:** 10 minutos de apresentação + 5 minutos de perguntas.
> **Slides:** [`slides.md`](slides.md) (formato Marp, exportável para PDF).
> **Apresentadores:** Higor Menezes · Narcélio Sousa

## Exportação para PDF

```bash
# Requer Node.js instalado
npx @marp-team/marp-cli docs/pitch/slides.md --pdf -o docs/pitch/slides.pdf
```

O deck em Markdown é o artefato versionado; o PDF é gerado localmente antes do Demo Day.

---

## Bloco 1 — Problema (1 min) · Slides 1–3

**Apresentador:** Higor

| Tempo | Conteúdo | Evidência |
| --- | --- | --- |
| 0:00–0:30 | Contexto: instituição financeira precisa decidir oferta/canal por cliente | Enunciado do Datathon |
| 0:30–1:00 | Dor: regras fixas e A/B longos desperdiçam tráfego; necessidade de personalização responsável | Problema de negócio |

**Fala-chave:** "Não estamos reproduzindo um banco real — demonstramos maturidade de MLE ponta a ponta."

---

## Bloco 2 — Abordagem e bandit (2 min) · Slides 4–5

**Apresentador:** Narcélio

| Tempo | Conteúdo | Evidência |
| --- | --- | --- |
| 1:00–1:30 | Base Kaggle (Bank Marketing) + camada sintética (5 braços, delayed rewards) | Etapas 1–2 |
| 1:30–2:00 | Algoritmos: baseline fixo, Thompson Sampling, UCB1 (Nilos-UCB) | Etapa 3 |
| 2:00–2:30 | Política servida: `context-greedy-v1` com guardrails auditáveis | Etapas 4–5 |
| 2:30–3:00 | Diagrama da arquitetura da solução (pipeline ponta a ponta) | `scripts/run_pipeline.py` |

**Fala-chave:** "Thompson Sampling venceu na simulação; o serving usa política contextual gulosa com trilhos de segurança."

---

## Bloco 3 — Demonstração ao vivo (3 min) · Slides 6–7

**Apresentador:** Narcélio (demo) · Higor (narrativa)

| Tempo | Conteúdo | Comando |
| --- | --- | --- |
| 3:00–3:30 | Subir API: `poetry run uvicorn src.service.app:app` | Terminal 1 |
| 3:30–4:00 | Caso típico (GS-T01): jovem + celular + sucesso → `arm_rate_boost` | `curl POST /decide` |
| 4:00–4:30 | Caso adversarial (GS-A03): jovem + stress + cold-start → `arm_control` | `curl POST /decide` |
| 4:30–5:00 | Caso suitability (GS-A04): incentivo bloqueado → `arm_retention_plus` | `curl POST /decide` |
| 5:00–5:30 | Mostrar log auditável: `GET /audit/{decision_id}` | Terminal 2 |
| 5:30–6:00 | Resumo: reason codes, policy_version, decision_id em cada resposta | Tela |

**Roteiro detalhado:** ver [`docs/demo-plan.md`](../demo-plan.md).

**Plano de contingência:** se API falhar, usar gravação ou Docker (`docker run -p 8000:8000 datathon-decision-api`).

---

## Bloco 4 — Evidências e métricas (2 min) · Slides 8–9

**Apresentador:** Higor

| Tempo | Conteúdo | Evidência |
| --- | --- | --- |
| 6:00–6:30 | Tabela bandit: Thompson Sampling regret 56.6 vs. baseline 1400 (96% redução) | `reports/offline-evaluation.md` |
| 6:30–7:00 | Golden set: 100% pass rate (24/24), incluindo 6 adversariais | `data/golden_set/evaluation_cases.jsonl` |
| 7:00–7:30 | Fairness: max/min ratio ≤ 1.26; sensibilidade a delayed rewards | `reports/figures/offline_fairness_exposure.png` |
| 7:30–8:00 | Ciclo MLOps: approval gate, MLflow, rollback demonstrável | `poetry run python -m src.mlops --approve` |

**Fala-chave:** "Toda promoção de política exige gate automático E aprovação humana."

---

## Bloco 5 — Arquitetura Azure + FinOps (1 min) · Slides 10–11

**Apresentador:** Higor

| Tempo | Conteúdo | Evidência |
| --- | --- | --- |
| 8:00–8:20 | Mapeamento local → Azure (Container Apps, APIM, ADLS, OpenAI, Key Vault) | `docs/architecture-azure.md` |
| 8:20–8:40 | **FinOps:** TCO dev ~$120–150/mês; prod 10k req/dia ~$600–900 | Tabela §8 do architecture-azure |
| 8:20–8:40 | **ROI:** regret 1400 → 56.6; golden set 100%; menos tráfego desperdiçado | Métricas reais |
| 8:40–9:00 | **Alternativas descartadas:** AKS (overhead), AWS/GCP (enunciado exige Azure), Functions (stateful) | §4 architecture-azure |
| 9:00–9:20 | **Cenários de escala:** 1k req/dia (1 réplica) → 100k (APIM Premium + AKS) | §8 architecture-azure |

**Fala-chave:** "Container Apps como primário; AKS só acima de 100k req/dia."

---

## Bloco 6 — Riscos e governança (1 min) · Slide 12

**Apresentador:** Narcélio

| Tempo | Conteúdo | Evidência |
| --- | --- | --- |
| 9:20–9:40 | 4 cenários de risco: reward hacking, manipulação de contexto, abuso RAG, suitability | `docs/system-card.md` §5 |
| 9:40–9:50 | Model card, system card, plano LGPD versionados | `docs/model-card.md`, `docs/lgpd-plan.md` |
| 9:50–10:00 | Revisão periódica: a cada promoção + trimestral | Model card §9 |

---

## Bloco 7 — Impacto e encerramento (0,5 min) · Slide 13

**Apresentador:** Ambos

| Tempo | Conteúdo |
| --- | --- |
| 10:00–10:30 | Entregue: pipeline reprodutível, API auditável, MLOps, governança completa |
| 10:30 | "Não alegamos prontidão para produção real regulada." |
| 10:30 | Perguntas? |

---

## FAQ antecipado (5 min de perguntas)

### P1: Por que não usar Thompson Sampling em produção?

A política servida (`context-greedy-v1`) prioriza **auditabilidade e determinismo** sobre exploração
estocástica. Thompson Sampling foi validado na simulação como melhor candidato adaptativo; o serving
usa roteamento contextual com guardrails testados no golden set (100% pass).

### P2: Como garantem que não há vazamento de dados?

Coluna `duration` (pós-contato) foi **descartada** com evidência quantitativa em
`reports/data-quality.md`. SHA-256 do arquivo bruto registrado em `metadata.json`.

### P3: Qual o custo real em Azure?

TCO dev ~$120–150/mês (AI Search domina). Prod 10k req/dia ~$600–900. Container Apps como primário;
AKS só para >100k req/dia. Detalhes em `docs/architecture-azure.md` §8.

### P4: Como funciona o approval gate?

Critérios automáticos (`golden_pass_rate ≥ 1.0`, `regret ≤ 300`, etc.) **E** aprovação humana.
Demonstrável: `poetry run python -m src.mlops --candidate v2 --approve --demo-rollback`.

### P5: E a LGPD?

Não há dados reais de titulares. Base pública sem PII + camada sintética. Plano LGPD documenta
minimização, retenção (90 dias em produção hipotética) e resposta a incidentes.

### P6: O que acontece se a política degradar em produção?

Monitoramento de PSI (drift) e `reward_trend`. PSI > 0.25 → alerta + rollback automático/manual
para versão anterior via `PolicyRegistry`.

### P7: Por que Bank Marketing e não outra base?

Aderência ao problema (campanhas bancárias, conversão como proxy de recompensa), rica em contexto
macroeconômico, vazamento documentável. Alternativas citadas no README.

---

## Checklist pré-apresentação

- [ ] API sobe sem erro (`poetry run uvicorn src.service.app:app`)
- [ ] 3 casos do golden set testados (GS-T01, GS-A03, GS-A04)
- [ ] Slides exportados para PDF (`npx @marp-team/marp-cli`)
- [ ] Gravação de backup pronta (se demo ao vivo)
- [ ] Docker image buildada (`docker build -t datathon-decision-api .`)
- [ ] `poetry run pytest -q` passa
- [ ] Links do repositório acessíveis
