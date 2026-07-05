# Geracao de dados — processo, sementes e riscos

> Documento consolidado exigido pelo enunciado do Datathon. Detalhes por camada
> estao em `data/kaggle/README.md`, `data/synthetic_enrichment/README.md` e
> `reports/data-quality.md`.

## 1. Pipeline de dados

```
Kaggle/UCI (bruto) → data/processed/ (sem vazamento) → data/synthetic_enrichment/ → golden set
```

| Etapa | Comando | Artefato |
| --- | --- | --- |
| 1 | `poetry run python -m src.data.prepare` | `data/processed/bank_marketing.parquet` |
| 2 | `notebooks/02_enriquecimento_sintetico.ipynb` | `offer_catalog`, `offer_events`, `delayed_rewards` |
| 4 | `data/golden_set/evaluation_cases.jsonl` | Casos versionados de avaliacao offline |

## 2. Sementes controladas (Etapa 2)

| Componente | Semente | Uso |
| --- | --- | --- |
| Catalogo de ofertas | `20240622` | Braços e metadados estaticos |
| Politica estocastica | `20240623` | Atribuicao de braços nos eventos |
| Recompensas | `20240624` | Recompensa intermediaria e atrasada |

Horizonte temporal: **14 dias**. Censura: recompensas positivas alem do horizonte marcadas como `censored`.

## 3. Hipoteses de modelagem

- **Target:** `subscribed` (proxy de conversao/recompensa final).
- **Vazamento:** coluna `duration` descartada (pos-contato).
- **Braços:** 5 ofertas sinteticas com `base_score` ordenando forca projetada.
- **Contexto:** segmentos derivados de idade, `pdays`, indicadores macro (`emp_var_rate`, `euribor3m`).
- **Ambiente bandit (Etapa 3):** taxas Bernoulli reescalonadas em `[0.04, 0.18]` pela ordem de `base_score`.
- **Politica contextual (Etapa 4):** scores lineares documentados em `src/evaluation/context_policy.py`.

## 4. Limitacoes

- Dados historicos (Portugal, 2008–2013); nao generalizam para 2026 sem retreino.
- Camada sintetica nao e causal; confundimento entre braço e desfecho no log original.
- Sem PII real; segmentos socioeconomicos com categoria `unknown`.

## 5. Riscos operacionais

| Risco | Mitigacao |
| --- | --- |
| Exploracao agressiva em cold-start | Trilhos de seguranca no golden set (Etapa 4) |
| Super-exposicao a incentivo financeiro | Casos adversariais + fairness por segmento |
| Feedback atrasado | Modelado em `delayed_rewards`; estudo de sensibilidade na Etapa 4 |
| Vazamento temporal | `duration` removida; decisoes documentadas em `reports/data-quality.md` |
