# Planejamento — Datathon 7MLET (Grupo 87)

> Plataforma de **experimentação adaptativa** (multi-armed bandit) para decidir qual
> oferta / mensagem / próximo passo apresentar a cada cliente elegível em canais
> digitais, no domínio financeiro regulado. O foco não é reproduzir um banco real,
> mas demonstrar **maturidade de Machine Learning Engineering** ponta a ponta:
> formular o problema, versionar dados, servir a decisão, avaliar qualidade,
> monitorar risco e governar o ciclo de vida.

**Equipe e divisão de trabalho:** cada integrante desenvolve **uma etapa por vez**.

| Integrante | Conta GitHub | Status |
|------------|--------------|--------|
| Higor Menezes | `higorms` | Etapas 0, 2 e 4 ✅ concluídas |
| Narcélio | `narcelio1989` (`nfilho1989`) | Etapas 1, 3 e 5 ✅ concluídas |

**Critério de avaliação oficial (Fase 05):**

| Dimensão | Peso | O que a banca procura |
|----------|------|------------------------|
| Critérios de negócio | 30% | Aderência ao problema, clareza de impacto, viabilidade, comunicação executiva |
| Validação técnica global | 70% | Pipeline, MLOps, avaliação, observabilidade, segurança, governança, documentação, uso de PyTorch/MLflow quando aplicável |

> ⚠️ **Regra de ouro:** as 9 etapas são **acumulativas**. Uma etapa posterior **não**
> compensa uma anterior ausente, e a falta de um subitem dentro de uma etapa **não**
> é compensada pelos demais subitens. Cada etapa tem uma **"evidência de aceite"** que
> a banca usa para considerá-la cumprida.

---

## Visão geral das 9 etapas obrigatórias (0–8)

| # | Etapa | Objetivo | Evidência de aceite (resumo) |
|---|-------|----------|------------------------------|
| **0** | Organização do projeto | Repositório público reutilizável por terceiros sem contexto oral | Pessoa externa instala deps, entende o fluxo e roda ≥1 comando de validação sozinha |
| **1** | Base Kaggle + EDA | Transformar base Kaggle compatível em fonte confiável | Banca rastreia origem do dataset, entende variáveis e confirma ausência de vazamento pós-contato |
| **2** | Enriquecimento sintético | Criar a camada de experimentação adaptativa sobre o dataset | Arquivos sintéticos com schema documentado e separados da base Kaggle original |
| **3** | Baseline + estratégia algorítmica | Comparar política simples vs. multi-armed bandit | Comparação quantitativa baseline × adaptativo, com justificativa de algoritmo, cold-start e delayed rewards |
| **4** | Avaliação offline + golden set | Medir qualidade e risco antes de servir | Métricas reproduzíveis, golden set versionado, análise de limitações/vieses |
| **5** | Serviço / interface demonstrável | Expor a decisão de forma controlada e auditável | Banca executa uma decisão de exemplo e vê braço, justificativa, versão da política e log auditável |
| **6** | Arquitetura-alvo Azure | Mostrar como seria operado em Azure | Arquitetura **exclusivamente Azure**, cobrindo todas as camadas, com Key Vault + Managed Identity |
| **7** | Ciclo de vida MLOps | Testar, aprovar e promover novas políticas | Demonstra hipótese saindo de experimento → produção controlada, com aprovação humana e rollback |
| **8** | Governança, Demo Day e relatórios | Fechar com responsabilidade operacional e narrativa | Narrativa coerente de problema → solução → evidências → riscos → governança → valor de negócio |

### Detalhe dos artefatos por etapa

#### Etapa 0 — Organização do projeto ✅ (Higor)
- [x] URL pública no padrão `datathon-7mlet-grupo-XX` → **`datathon-7mlet-grupo-87`**
- [x] `pyproject.toml` (deps, versão de Python, ferramentas dev)
- [x] `.env.example` (variáveis necessárias, sem valores reais)
- [x] Licença (MIT) e `.gitignore`
- [ ] **README.md completo** (visão do problema, escopo, escolhas de design, execução local, mapa de pastas, comandos, limitações) → *atualmente quase vazio; precisa ser complementado*
- [x] Histórico de commits que mostre evolução

> 📌 **Pendências da Etapa 0 a alinhar com o Higor:** README ainda mínimo e `.gitignore`
> ignora toda a pasta `data/`, o que impede versionar artefatos exigidos a partir da
> Etapa 1 (ver ajuste na Etapa 1 abaixo).

#### Etapa 1 — Base Kaggle e EDA 🔜
- `data/kaggle/README.md` (link, versão, fonte, licença, limitações, instruções de download)
- Dicionário de dados, notebook de EDA e relatório de qualidade
- Camada de dados em código que carrega a base, registra fonte/versão/licença e gera os datasets derivados
- Decisão documentada sobre colunas com vazamento temporal/pós-contato (ex.: `duration`)

#### Etapa 2 — Enriquecimento sintético
- `data/synthetic_enrichment/` com `offer_catalog`, `offer_events`, `delayed_rewards`
- Catálogo de braços/ofertas **separado fisicamente** da base Kaggle
- Eventos de impressão, contexto de decisão e recompensas com **sementes controladas**
- Modelagem de delayed rewards e horizonte temporal documentada + schema descrito

#### Etapa 3 — Baseline e estratégia algorítmica
- ≥1 baseline determinístico (regra fixa / melhor braço histórico / segmentação)
- Implementação/simulação de **Thompson Sampling** (priors documentados)
- Referência/justificativa de **Nilos-UCB** (família UCB) na análise
- Métricas: recompensa, **regret**, exploração, conversão simulada
- Tratamento de **cold-start** e **delayed rewards**

#### Etapa 4 — Avaliação offline e golden set
- Script/notebook de avaliação offline **reproduzível** por CLI/notebook
- `data/golden_set/evaluation_cases.jsonl` com **≥20 casos** versionados
- Cobertura: casos típicos, borda, segmentos elegíveis, cenários adversariais
- Cada caso: contexto, ação esperada, recompensa esperada, justificativa, critério pass/fail
- Matriz de métricas, análise de sensibilidade e **fairness de exposição** entre segmentos

#### Etapa 5 — Serviço ou interface demonstrável
- API / CLI / notebook executável que recebe contexto → devolve decisão
- Contrato de entrada/saída documentado, com exemplo e tratamento de erro
- **Log auditável** com reason codes, braço selecionado e versão da política
- Comando único para reproduzir o pipeline ponta a ponta local
- Suíte mínima de testes (contratos de dados, política, registro de decisão)

#### Etapa 6 — Arquitetura-alvo Azure
- `docs/architecture-azure.md` com **diagrama Mermaid** e mapeamento de serviços Azure
- Plano de deploy + estimativa qualitativa de custo
- Camadas: compute, API, dados, IA/RAG, observabilidade, segurança, identidade, governança
- Gestão de segredos com **Azure Key Vault** e **Managed Identity** (somente Azure)

#### Etapa 7 — Ciclo de vida MLOps
- Plano de retreino: critérios de promoção, **approval gate**, rollback, versionamento de política
- Monitoramento de **drift** e de recompensa
- Rastreio de experimentos em **MLflow** (ou equivalente)
- Procedimento de teste + aprovação humana estruturada + promoção controlada

#### Etapa 8 — Governança, Demo Day e relatórios
- `docs/model-card.md`, `docs/system-card.md`, `docs/lgpd-plan.md`
- Relatório técnico (≤10 páginas)
- Pitch (≤10 min + 5 min de perguntas) com slides versionados
- FinOps (ROI, custo por serviço Azure, TCO), justificativa de arquitetura, cenários de escala
- (Desejável / pontos extras) demonstração ao vivo ou gravada com plano de contingência

---

## Planejamento detalhado — Etapa 1: Base Kaggle e EDA

**Responsável:** Narcélio · **Objetivo:** transformar uma base Kaggle compatível
numa fonte confiável e rastreável para a experimentação adaptativa, **sem vazamento**.

### Evidência de aceite a atingir
> A banca consegue (1) rastrear a origem do dataset (fonte/versão/licença), (2) entender
> as variáveis usadas e (3) **verificar que não houve vazamento de informação
> pós-contato** no modelo de decisão.

### Decisão da base Kaggle
Recomendação: **`bank-marketing` (henriqueyamahata)** como base principal.
- Aderente ao problema (campanhas bancárias, propensão de conversão, decisão de oferta).
- `target` = `y` (cliente assinou depósito a prazo: sim/não) → proxy de conversão/recompensa.
- Bem documentada e amplamente referenciada → facilita dicionário de dados.
- Permite, na Etapa 2, mapear features → contexto e a oferta → braço do bandit.

> Bases alternativas (`tunguz`, `dharmik34`, `aguado`) são aceitas se justificarmos a
> aderência e documentarmos fonte/versão/licença/colunas/target/limitações. Manteremos
> `bank-marketing` como principal e podemos citar as outras como comparação futura.

### ⚠️ Vazamento temporal — decisão obrigatória
- **Descartar `duration`** (duração da última ligação): só é conhecida *após* o contato e
  é quase perfeitamente correlacionada com o `y` → vazamento pós-contato clássico.
- Revisar também `pdays`, `previous`, `poutcome` e features de campanha que só existem
  *após* a decisão de contatar — documentar tratamento ou descarte de cada uma.
- A decisão de cada coluna fica registrada no relatório de qualidade (com justificativa).

### Estrutura de pastas a criar (Etapa 1)
```
data/
  kaggle/
    README.md            # fonte, link, versão, licença, limitações, instruções de download
    raw/                 # CSV bruto do Kaggle (NÃO versionado — baixado via script)
  processed/
    bank_marketing.parquet  # base tratada, sem vazamento (artefato derivado)
src/
  data/
    __init__.py
    load.py              # carrega base, registra fonte/versão/licença
    build_processed.py   # gera datasets derivados documentados (remove vazamento)
    schema.py            # dicionário de dados / tipos / contratos
notebooks/
  01_eda.ipynb           # EDA exploratória
reports/
  data-quality.md        # relatório de qualidade + decisões de vazamento
  data-dictionary.md     # dicionário de dados
```

### ⚠️ Ajuste necessário no `.gitignore`
O `.gitignore` atual ignora **toda** a pasta `data/` e `*.csv`/`*.parquet`. Precisamos:
- **Manter ignorado:** `data/kaggle/raw/` e o CSV bruto do Kaggle (não versionar dado bruto).
- **Passar a versionar:** `data/kaggle/README.md`, `data/processed/` (artefato derivado
  pequeno), e mais tarde `data/synthetic_enrichment/` e `data/golden_set/`.
- Estratégia: ignorar `data/` por padrão e usar exceções (`!data/.../`) para os artefatos
  que devem entrar no controle de versão.

### Passos de execução
1. **Alinhar com Higor** o ajuste do `.gitignore` e completar o README da Etapa 0.
2. **Adicionar dependências** ao `pyproject.toml` (Poetry): `pandas`, `numpy`,
   `matplotlib`/`seaborn`, `jupyter`, `pyarrow`, `pydantic` (contratos) e `kagglehub`
   (download reprodutível) — `pytest` em dev.
3. Criar `data/kaggle/README.md` com fonte, link, versão, licença, limitações e
   instruções de download (preferir download programático e reprodutível).
4. Implementar `src/data/load.py` (carrega base + registra metadados) e
   `src/data/build_processed.py` (gera `data/processed/` sem vazamento).
5. Escrever `reports/data-dictionary.md` (cada coluna: tipo, descrição, papel) e
   `reports/data-quality.md` (nulos, duplicatas, distribuição do target, outliers,
   **decisão sobre vazamento coluna a coluna**).
6. Desenvolver `notebooks/01_eda.ipynb`: distribuição do target (desbalanceamento),
   features categóricas/numéricas, correlações, evidência visual de por que `duration`
   vaza, e identificação de **segmentos** que serão úteis no bandit (Etapa 2).
7. Garantir **reprodutibilidade**: um comando documentado (ex.: `poetry run python -m
   src.data.build_processed`) que baixa/trata e gera os artefatos derivados.
8. Atualizar o README com a seção da Etapa 1 (como baixar, como rodar, o que é gerado).
9. **Commits incrementais** assinados pela conta `narcelio1989` mostrando evolução.

### Checklist de aceite da Etapa 1
- [ ] `data/kaggle/README.md` com link, versão, fonte, licença, limitações e instruções de download
- [ ] Dicionário de dados (`reports/data-dictionary.md`)
- [ ] Notebook de EDA (`notebooks/01_eda.ipynb`)
- [ ] Relatório de qualidade (`reports/data-quality.md`)
- [ ] Camada de dados em código que carrega a base e registra fonte/versão/licença
- [ ] Geração reprodutível de `data/processed/` (datasets derivados documentados)
- [ ] Decisão documentada de vazamento (`duration` e correlatas), com justificativa
- [ ] `.gitignore` ajustado para versionar artefatos derivados (e não o dado bruto)
- [ ] README atualizado com instruções da Etapa 1
