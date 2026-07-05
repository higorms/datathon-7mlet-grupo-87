# datathon-7mlet-grupo-87

Plataforma de **experimentação adaptativa** (multi-armed bandit) para decidir qual
**oferta / mensagem / próximo passo** apresentar a cada cliente elegível em canais
digitais, no domínio financeiro. Projeto do **Datathon 7MLET (Fase 05)**.

> O objetivo não é reproduzir um sistema bancário real, e sim demonstrar maturidade de
> **Machine Learning Engineering** ponta a ponta: formular o problema, versionar dados,
> servir a decisão, avaliar qualidade, monitorar risco e governar o ciclo de vida.

## Visão do problema

Regras fixas e testes A/B longos desperdiçam tráfego e demoram a reagir a mudanças de
contexto. Uma abordagem de **multi-armed bandit** equilibra exploração e explotação,
aprendendo com as respostas observadas. Sobre uma base pública de marketing bancário,
construímos uma camada sintética de experimentação (ofertas, contexto, recompensas) e
um assistente com LLM que resume experimentos e explica decisões.

## Escopo e escolhas de design

- **Base factual:** Bank Marketing (`bank-additional-full`) — campanhas de telemarketing
  bancário; o alvo "assinou depósito a prazo" é o **proxy de conversão/recompensa**.
- **Sem vazamento:** a coluna `duration` (conhecida só após o contato) é **descartada**.
- **Camada de dados em código** (`src/data/`) com proveniência rastreável (fonte, versão,
  licença, SHA-256) e geração reprodutível dos artefatos derivados.
- **Gestão de ambiente:** Poetry (Python ≥ 3.12). Dados brutos não versionados; apenas
  artefatos derivados (`data/processed/`) e documentação entram no repositório.

## Mapa de pastas

```
datathon-7mlet-grupo-87/
├── data/
│   ├── kaggle/
│   │   ├── README.md            # fonte, link, versão, licença, limitações, download
│   │   └── raw/                 # CSV bruto (NÃO versionado — baixado via script)
│   ├── processed/
│   │   ├── bank_marketing.parquet  # base tratada, sem vazamento (versionada)
│   │   └── metadata.json           # proveniência + resumo do processamento
│   ├── synthetic_enrichment/    # camada sintética (Etapa 2)
│   └── golden_set/              # golden set de avaliação offline (Etapa 4)
├── notebooks/
│   ├── 01_eda.ipynb             # EDA executada (Etapa 1)
│   ├── 02_enriquecimento_sintetico.ipynb  # camada sintética (Etapa 2)
│   ├── 03_baseline_bandit.ipynb # baseline x bandit (Etapa 3)
│   └── 04_avaliacao_offline.ipynb # avaliação offline + golden set (Etapa 4)
├── reports/
│   ├── data-dictionary.md       # dicionário de dados
│   ├── data-quality.md          # relatório de qualidade (gerado)
│   ├── data-generation.md       # processo, sementes, hipóteses e riscos
│   ├── bandit-comparison.md     # comparação baseline x bandit (gerado)
│   ├── bandit-metrics.json      # métricas do experimento (gerado)
│   ├── offline-evaluation.md    # avaliação offline + golden set (gerado)
│   ├── offline-metrics.json     # métricas da Etapa 4 (gerado)
│   └── figures/                 # figuras da EDA, bandit e avaliação offline
├── src/
│   ├── data/                    # camada de dados (download, load, processamento, qualidade)
│   ├── bandits/                 # políticas, ambiente, simulação e experimento (Etapa 3)
│   └── evaluation/              # golden set, fairness e avaliação offline (Etapa 4)
├── tests/                       # testes de validação (camada de dados e bandits)
├── PLANEJAMENTO.md              # plano das 9 etapas (0–8)
├── pyproject.toml               # dependências e configuração (Poetry)
└── .env.example                 # variáveis de ambiente (credencial Kaggle opcional)
```

## Execução local

Pré-requisitos: **Python ≥ 3.12** e **Poetry**.

```bash
# 1. Instalar dependências (cria o ambiente virtual .venv)
poetry install

# 2. (Opcional) credencial Kaggle: copie .env.example para .env e preencha.
#    Sem credencial o download é anônimo/UCI e funciona normalmente.
cp .env.example .env

# 3. Pipeline da Etapa 1 ponta a ponta (download -> processado -> relatório de qualidade)
poetry run python -m src.data.prepare

# 4. Experimento da Etapa 3 (baseline x bandit -> relatório + figuras)
poetry run python -m src.bandits.experiment

# 5. Avaliação offline da Etapa 4 (golden set + métricas + fairness)
poetry run python -m src.evaluation

# 6. (Opcional) reexecutar os notebooks
poetry run jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb

# 7. Testes de validação
poetry run pytest -q
```

## Lista de comandos

| Comando | O que faz |
| --- | --- |
| `poetry install` | Instala dependências no `.venv`. |
| `poetry run python -m src.data.prepare` | **Comando único** da Etapa 1: baixa, processa e gera o relatório. |
| `poetry run python -m src.data.download [--source uci\|kaggle] [--force]` | Só baixa a base bruta. |
| `poetry run python -m src.data.build_processed` | Gera `data/processed/` sem vazamento. |
| `poetry run python -m src.bandits.experiment [--horizon N --seeds N]` | **Etapa 3:** compara baseline x bandit e gera relatório/figuras. |
| `poetry run python -m src.evaluation [--horizon N --seeds N]` | **Etapa 4:** avalia golden set, sensibilidade, fairness e gera relatório. |
| `poetry run pytest -q` | Roda os testes de validação (dados, bandits e avaliação). |
| `poetry run ruff check src/` | Lint do código-fonte. |

## Etapas do projeto

Plano completo das 9 etapas em [`PLANEJAMENTO.md`](PLANEJAMENTO.md).

- **Etapa 0 — Organização** ✅ (repo, licença, pyproject, .env.example)
- **Etapa 1 — Base Kaggle e EDA** ✅
  - Documentação da base: [`data/kaggle/README.md`](data/kaggle/README.md)
  - Dicionário de dados: [`reports/data-dictionary.md`](reports/data-dictionary.md)
  - Relatório de qualidade: [`reports/data-quality.md`](reports/data-quality.md)
  - EDA: [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb)
  - Camada de dados: [`src/data/`](src/data/)
- **Etapa 2 — Enriquecimento sintético** ✅
  - Documentação/schema: [`data/synthetic_enrichment/README.md`](data/synthetic_enrichment/README.md)
  - Notebook gerador: [`notebooks/02_enriquecimento_sintetico.ipynb`](notebooks/02_enriquecimento_sintetico.ipynb)
  - Artefatos: `offer_catalog`, `offer_events`, `delayed_rewards` (parquet)
- **Etapa 3 — Baseline e estratégia algorítmica** ✅
  - Comparação (gerada): [`reports/bandit-comparison.md`](reports/bandit-comparison.md)
  - Notebook: [`notebooks/03_baseline_bandit.ipynb`](notebooks/03_baseline_bandit.ipynb)
  - Código (políticas/ambiente/simulação): [`src/bandits/`](src/bandits/)
- **Etapa 4 — Avaliação offline e golden set** ✅
  - Golden set: [`data/golden_set/evaluation_cases.jsonl`](data/golden_set/evaluation_cases.jsonl) (24 casos)
  - Documentação: [`data/golden_set/README.md`](data/golden_set/README.md)
  - Relatório (gerado): [`reports/offline-evaluation.md`](reports/offline-evaluation.md)
  - Notebook: [`notebooks/04_avaliacao_offline.ipynb`](notebooks/04_avaliacao_offline.ipynb)
  - Código: [`src/evaluation/`](src/evaluation/)
- **Etapas 5–8** — planejadas (ver `PLANEJAMENTO.md`).

## Limitações conhecidas

- Base estática (instituição portuguesa, 2008–2013); indicadores macro refletem o
  período da crise e não generalizam sem ressalvas.
- **Desbalanceamento forte** (~11,7% de conversões) — exige métricas além da acurácia.
- Colunas socioeconômicas com `unknown` (até ~21% em `default`); não imputadas na Etapa 1.
- Não há dados reais de clientes identificáveis; nenhum identificador pessoal, renda,
  patrimônio, gênero ou raça é utilizado.

## Licença

Código sob licença **MIT** (ver [`LICENSE`](LICENSE)). A base de dados é distribuída sob
**CC BY 4.0** (UCI Machine Learning Repository) — atribuição em `data/kaggle/README.md`.
