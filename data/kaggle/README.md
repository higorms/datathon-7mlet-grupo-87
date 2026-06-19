# Base Kaggle — Bank Marketing

Documentação da base de referência factual usada no projeto (Etapa 1). A camada
sintética de experimentação adaptativa (Etapa 2) será construída **sobre** esta base,
mas mantida fisicamente separada.

## Fonte e link

| Campo | Valor |
| --- | --- |
| **Nome** | Bank Marketing (arquivo `bank-additional-full.csv`) |
| **Kaggle (referência primária)** | https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing |
| **Fonte factual original (UCI)** | https://archive.ics.uci.edu/dataset/222/bank+marketing |
| **DOI** | https://doi.org/10.24432/C5K306 |
| **Autoria** | S. Moro, P. Rita, P. Cortez (2014) |

> O dataset do Kaggle (`henriqueyamahata/bank-marketing`) é um **espelho** do dataset
> 222 do UCI Machine Learning Repository. Documentamos os dois para máxima
> rastreabilidade: usamos o Kaggle como referência exigida pelo desafio e a UCI como
> fonte canônica/fallback público de download.

## Versão

- **Versão:** UCI 2014-02-13 (Moro et al., 2014). A base é **estática** desde a
  publicação — não há releases incrementais.
- **Arquivo canônico:** `bank-additional-full.csv` (41.188 linhas × 21 colunas;
  separador `;`). É a versão "additional", que inclui 5 indicadores socioeconômicos
  ausentes na versão antiga `bank-full.csv`.
- **Integridade:** o SHA-256 do arquivo bruto é registrado em
  `data/processed/metadata.json` (campo `provenance.raw_sha256`) a cada execução do
  pipeline, fixando a versão exata dos dados usados.

## Licença

- **CC BY 4.0** (UCI Machine Learning Repository). Uso permitido com atribuição.
- **Citação exigida:**
  > Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI Machine
  > Learning Repository. https://doi.org/10.24432/C5K306

## Por que esta base

- **Aderência ao desafio:** campanhas de marketing bancário (telemarketing de depósito
  a prazo). O alvo `y` (cliente assinou: sim/não) é um **proxy natural de conversão**,
  exatamente o sinal que o multi-armed bandit otimiza.
- **Rica em contexto:** inclui indicadores macroeconômicos (`emp.var.rate`,
  `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed`) — base ideal para a
  decisão **contextual** das próximas etapas.
- **Vazamento documentável:** a coluna `duration` é um caso clássico de vazamento
  pós-contato, que a própria UCI orienta descartar (ver "Limitações").

## Como baixar

O download é feito pela camada de dados em código, com dois caminhos automáticos:

```bash
# Caminho 1 (default): kagglehub. Funciona de forma anônima para datasets públicos;
# usa credencial (KAGGLE_USERNAME/KAGGLE_KEY do .env) se disponível.
poetry run python -m src.data.download

# Caminho 2: forçar o fallback público da UCI (não exige credencial Kaggle).
poetry run python -m src.data.download --source uci
```

O arquivo bruto é salvo em `data/kaggle/raw/bank-additional-full.csv`, que **não é
versionado** (ver `.gitignore`). Apenas os artefatos derivados (`data/processed/`) e
esta documentação entram no controle de versão.

> **Credencial Kaggle (opcional):** copie `.env.example` para `.env` e preencha
> `KAGGLE_USERNAME` e `KAGGLE_KEY` (campos do `kaggle.json` baixado em
> kaggle.com → Settings → API). Sem credencial, o download anônimo/UCI cobre tudo.

## Limitações e riscos conhecidos

1. **Vazamento — `duration`:** só é conhecida após o término da ligação (quando o
   desfecho já existe). **Descartada** do dataset de decisão. Evidência quantitativa
   em [`reports/data-quality.md`](../../reports/data-quality.md) (seção 7).
2. **Forte desbalanceamento:** apenas **11,67%** de conversões — exige métricas além
   da acurácia (AUC-PR, recall, lift) e cuidado no design de recompensa do bandit.
3. **Ausência disfarçada de `unknown`:** colunas socioeconômicas usam o token
   `"unknown"` em vez de célula vazia. Destaque para `default` com **~21%** de
   `unknown`. Tratado como categoria própria na Etapa 1 (sem imputação).
4. **Sentinela `pdays == 999`:** ~96% dos clientes nunca foram contatados antes; `999`
   é um marcador, **não** um valor contínuo — não pode entrar como número "cru" em
   modelos sensíveis a escala sem tratamento.
5. **Dados não são de clientes reais identificáveis** e não devem ser tratados como
   tal. Nenhum identificador pessoal, renda, patrimônio, gênero ou raça é usado, em
   linha com as restrições do desafio.
6. **Representatividade temporal:** coleta de uma instituição portuguesa (2008–2013),
   período da crise financeira — os indicadores macroeconômicos refletem esse contexto
   e não generalizam para outros mercados/épocas sem ressalvas.

## Arquivos relacionados

- Dicionário de dados: [`reports/data-dictionary.md`](../../reports/data-dictionary.md)
- Relatório de qualidade: [`reports/data-quality.md`](../../reports/data-quality.md)
- Metadados de proveniência (gerados): `data/processed/metadata.json`
- Notebook de EDA: [`notebooks/01_eda.ipynb`](../../notebooks/01_eda.ipynb)
