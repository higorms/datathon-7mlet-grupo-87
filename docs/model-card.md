# Model Card — Datathon 7MLET (Grupo 87)

> **Etapa 8** · Documentação de governança da política de decisão adaptativa.
> Última revisão: 2026-07-23 · Versão do documento: 1.0

## 1. Nome e versão

| Campo | Valor |
| --- | --- |
| **Nome** | Política contextual de oferta bancária (multi-armed bandit) |
| **Versão servida (produção)** | `context-greedy-v1` ([`src/service/policy_meta.py`](../src/service/policy_meta.py)) |
| **Registro MLOps** | [`mlops/policy_registry.json`](../mlops/policy_registry.json) |
| **Políticas de simulação (Etapa 3)** | Baseline fixo, Epsilon-greedy, UCB1 (Nilos-UCB), Thompson Sampling |

### Distinção importante: simulação vs. serving

| Camada | Política | Papel |
| --- | --- | --- |
| **Simulação (Etapa 3)** | Thompson Sampling, UCB1, baseline fixo | Comparação quantitativa (regret, exploração, conversão) |
| **Serving (Etapas 4/5)** | `context-greedy-v1` (gulosa contextual + trilhos de segurança) | Decisão auditável em produção controlada |

A política servida **não** é Thompson Sampling em tempo real. Thompson Sampling foi escolhido como
melhor candidato adaptativo na simulação; o serving usa roteamento contextual determinístico com
guardrails validados pelo golden set (100% pass rate).

## 2. Dados de treino e avaliação

| Fonte | Descrição | Licença |
| --- | --- | --- |
| **Bank Marketing** (UCI/Kaggle) | Base factual de campanhas bancárias; target `subscribed` como proxy de conversão | CC BY 4.0 |
| **Camada sintética** (Etapa 2) | `offer_catalog`, `offer_events`, `delayed_rewards` — braços, contexto e recompensas atrasadas | Derivada, sem PII |
| **Golden set** (Etapa 4) | 24 casos versionados em `data/golden_set/evaluation_cases.jsonl` | Sintético |

- **Proveniência:** documentada em [`data/kaggle/README.md`](../data/kaggle/README.md) e
  [`reports/data-generation.md`](../reports/data-generation.md).
- **Vazamento tratado:** coluna `duration` (pós-contato) **descartada** — ver
  [`reports/data-quality.md`](../reports/data-quality.md).
- **Sementes controladas:** catálogo `20240622`, política `20240623`, recompensas `20240624`.

## 3. Métricas de avaliação

### 3.1 Políticas bandit (simulação — Etapa 3)

Configuração: horizonte 10.000, 15 sementes ([`reports/offline-evaluation.md`](../reports/offline-evaluation.md)).

| Política | Recompensa | Conversão | Regret final | Exploração | % braço ótimo |
| --- | --- | --- | --- | --- | --- |
| Baseline fixo (controle) | 403 | 4.03% | 1400.0 ± 0.0 | 0.0% | 0.0% |
| Epsilon-greedy (ε=0.1) | 1645 | 16.45% | 147.7 ± 93.9 | 8.0% | 70.1% |
| UCB1 (Nilos-UCB) | 1514 | 15.14% | 293.9 ± 26.2 | 44.6% | 55.0% |
| **Thompson Sampling** | **1738** | **17.38%** | **56.6 ± 15.7** | **9.0%** | **90.2%** |

### 3.2 Política servida (golden set — Etapa 4)

| Métrica | Valor |
| --- | --- |
| **Pass rate global** | 100% (24/24 casos) |
| Pass rate adversarial | 100% (6/6) |
| Pass rate edge | 100% (6/6) |
| Pass rate segment | 100% (6/6) |
| Pass rate typical | 100% (6/6) |

### 3.3 Métricas do registro MLOps (`context-greedy-v1`)

| Métrica | Valor |
| --- | --- |
| `golden_pass_rate` | 1.0 |
| `fallback_rate` | 0.25 |
| `regret` | 56.6 |
| `optimal_arm_rate` | 0.94 |

## 4. Intended use (uso pretendido)

- **Apoio à decisão** de qual oferta/mensagem apresentar a clientes elegíveis em canais digitais,
  em ambiente de **experimentação controlada** (PoC / datathon).
- Comparação de políticas adaptativas (bandit) vs. baseline determinístico para demonstrar ganho
  de exploração/explotação.
- Avaliação offline de risco antes de promover novas versões de política (approval gate, Etapa 7).
- Explicação de decisões via reason codes auditáveis e assistente RAG (arquitetura-alvo Azure).

**Humano no loop:** decisões sensíveis (perfil de alto risco, exceções de suitability) exigem
revisão humana antes de qualquer promoção para produção real.

## 5. Out-of-scope (uso fora do escopo)

- **Não** usar para decisão de crédito, patrimônio, renda ou scoring regulatório.
- **Não** usar com dados reais de clientes identificáveis (o projeto usa apenas base pública + camada sintética).
- **Não** promover políticas sem passar pelo approval gate (`golden_pass_rate ≥ 1.0`, `regret ≤ 300`, etc.).
- **Não** aplicar automaticamente em cenários fora dos segmentos sintéticos modelados (macro stress +
  cold-start sem histórico → revisão humana obrigatória).
- **Não** alegar prontidão para produção real regulada — este é um demonstrador de maturidade MLE.

## 6. Análise de fairness

Comparação de exposição ao braço ótimo (`arm_rate_boost`) entre segmentos sintéticos
([`reports/offline-evaluation.md`](../reports/offline-evaluation.md) §4):

| Dimensão | Grupos | Max/min ratio (ótimo) | Std exposição ótimo |
| --- | --- | --- | --- |
| `segment_age_band` | 6 | 1.257 | 0.0299 |
| `segment_history` | 2 | 1.028 | 0.005 |
| `segment_macro_regime` | 3 | 1.043 | 0.0055 |

> Ratio max/min elevado em `segment_age_band` indica desigualdade de exposição ao braço ótimo entre
> faixas etárias — revisar caps de exploração antes de escalar.

## 7. Vieses conhecidos

| Viés | Descrição | Mitigação |
| --- | --- | --- |
| **Celular → incentivo financeiro** | Canal `cellular` infla sistematicamente `arm_rate_boost` | Casos adversariais no golden set; fairness por segmento |
| **Cold-start agressivo** | Perfis novos tendem a ofertas de maior score sem histórico | Trilho `SAFE_FALLBACK_HIGH_RISK` (jovem + stress + cold-start) |
| **Exploração estocástica** | Thompson Sampling pode super-expor braços sub-ótimos em segmentos vulneráveis | Política servida é gulosa (não estocástica); caps documentados |
| **Base histórica** | Dados de Portugal 2008–2013; indicadores macro refletem crise financeira | Documentado como limitação; retreino obrigatório para outros contextos |
| **Não causal** | Camada sintética não estabelece causalidade braço → desfecho | Golden set + análise de sensibilidade; não inferir causalidade |

## 8. Limitações técnicas

- Base **estática** (Bank Marketing 2008–2013); scores contextuais **não são causais**.
- **Desbalanceamento** de conversão (~11,7%) — métricas de acurácia são insuficientes.
- Simulação bandit (Etapa 3) é **não-contextual**; golden set avalia roteamento contextual — camadas distintas e complementares.
- Fairness calculada sobre amostra de eventos sintéticos; segmentos raros têm alta variância.
- Feedback atrasado degrada regret mensuravelmente (estudo de sensibilidade na Etapa 4).

### Quando NÃO usar a política automaticamente

- Contexto **incompleto** (canal desconhecido, flags de fallback) → `arm_control`.
- **Macro stress** + jovem + cold-start sem histórico → revisão humana obrigatória.
- Cliente **não elegível** a incentivo financeiro (`financial_incentive_blocked`) → nunca `arm_rate_boost`.
- Segmentos com **sub-exposição** ao braço adequado → cap de exploração ou política segmentada.
- Ambiente com **feedback altamente atrasado** (delay > 200 rodadas) → degradação mensurável do regret.

## 9. Plano de revisão periódica

| Evento | Responsável | Ação |
| --- | --- | --- |
| Promoção de `policy_version` | Narcélio (MLOps) | Atualizar model card com novas métricas do approval gate |
| Revisão trimestral fixa | Higor (dados/governança) | Revisar fairness, limitações e vieses conhecidos |
| Incidente de drift (PSI > 0.25) | Equipe (ambos) | Revisão emergencial + possível rollback |
| Mudança de base Kaggle ou catálogo | Higor | Revalidar proveniência, golden set e métricas |
| Alteração de guardrails/reason codes | Narcélio | Atualizar seções 6–8 e reexecutar golden set |

**Cadência:** revisão obrigatória a cada promoção de política + revisão trimestral programada.
**Versionamento:** este documento é versionado no repositório; alterações via PR com aprovação de ambos os integrantes.

## Referências

- Relatório offline: [`reports/offline-evaluation.md`](../reports/offline-evaluation.md)
- Comparação bandit: [`reports/bandit-comparison.md`](../reports/bandit-comparison.md)
- Ciclo MLOps: [`docs/mlops-lifecycle.md`](mlops-lifecycle.md)
- System card: [`docs/system-card.md`](system-card.md)
- Plano LGPD: [`docs/lgpd-plan.md`](lgpd-plan.md)
