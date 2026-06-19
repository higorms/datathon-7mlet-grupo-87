"""Proveniencia da base e decisao de vazamento, centralizadas em um unico lugar.

Manter esses metadados em codigo (e nao espalhados em notebooks) garante que a
camada de dados, o relatorio de qualidade e a EDA falem exatamente da mesma fonte,
versao, licenca e das mesmas regras de descarte de colunas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Caminhos do projeto
# --------------------------------------------------------------------------- #
# .../src/data/metadata.py -> sobe 3 niveis ate a raiz do repositorio.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "kaggle" / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

#: Nome canonico do arquivo bruto que usamos como base principal.
RAW_FILENAME: str = "bank-additional-full.csv"
#: Separador do CSV original (UCI/Kaggle usam ponto-e-virgula).
CSV_SEPARATOR: str = ";"

# Artefatos derivados versionados (Etapa 1).
PROCESSED_PARQUET: Path = PROCESSED_DIR / "bank_marketing.parquet"
PROCESSED_METADATA_JSON: Path = PROCESSED_DIR / "metadata.json"


# --------------------------------------------------------------------------- #
# Proveniencia da base
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DatasetSource:
    """Fonte, versao e licenca da base, com os dois caminhos de download."""

    name: str = "Bank Marketing (bank-additional-full)"
    # Referencia primaria exigida pelo desafio: dataset no Kaggle.
    kaggle_slug: str = "henriqueyamahata/bank-marketing"
    kaggle_url: str = "https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing"
    # Fonte factual original (a base do Kaggle e um espelho desta).
    uci_id: int = 222
    uci_url: str = "https://archive.ics.uci.edu/dataset/222/bank+marketing"
    uci_download_url: str = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"
    # Versao: a base e estatica desde 2014; usamos a data de publicacao na UCI.
    version: str = "UCI 2014-02-13 (Moro et al., 2014)"
    license: str = "CC BY 4.0 (UCI Machine Learning Repository)"
    citation: str = (
        "Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing [Dataset]. "
        "UCI Machine Learning Repository. https://doi.org/10.24432/C5K306"
    )


SOURCE = DatasetSource()


# --------------------------------------------------------------------------- #
# Esquema de colunas
# --------------------------------------------------------------------------- #
#: Coluna alvo original (string 'yes'/'no').
RAW_TARGET: str = "y"
#: Nome da coluna alvo no dataset processado (inteiro 0/1).
TARGET: str = "subscribed"

#: Renomeacao de colunas com ponto para nomes amigaveis a codigo (e a df.query).
RENAME_MAP: dict[str, str] = {
    "emp.var.rate": "emp_var_rate",
    "cons.price.idx": "cons_price_idx",
    "cons.conf.idx": "cons_conf_idx",
    "nr.employed": "nr_employed",
}

#: Colunas categoricas (apos a renomeacao).
CATEGORICAL_COLUMNS: tuple[str, ...] = (
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "poutcome",
)

#: Colunas numericas mantidas no dataset de decisao (apos remover vazamento).
NUMERIC_COLUMNS: tuple[str, ...] = (
    "age",
    "campaign",
    "pdays",
    "previous",
    "emp_var_rate",
    "cons_price_idx",
    "cons_conf_idx",
    "euribor3m",
    "nr_employed",
)

#: Valor sentinela de pdays que significa "cliente nunca foi contatado antes".
PDAYS_NOT_CONTACTED: int = 999

#: Categorias que representam dado ausente (nao sao 'NaN' no CSV original).
MISSING_CATEGORY_TOKEN: str = "unknown"


# --------------------------------------------------------------------------- #
# Decisao de vazamento (temporal / pos-contato)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LeakageDecision:
    """Decisao explicita sobre uma coluna potencialmente vazante."""

    column: str
    decision: str  # "descartar" | "manter"
    rationale: str


#: Decisoes documentadas. `duration` e o caso classico de vazamento pos-contato.
LEAKAGE_DECISIONS: tuple[LeakageDecision, ...] = (
    LeakageDecision(
        column="duration",
        decision="descartar",
        rationale=(
            "Duracao em segundos do ultimo contato. So e conhecida APOS a ligacao "
            "terminar e, nesse ponto, o resultado y ja e conhecido (duration=0 => y='no'). "
            "A propria UCI orienta descartar a coluna para um modelo preditivo realista. "
            "Mante-la causaria vazamento pos-contato e infla artificialmente a metrica."
        ),
    ),
    LeakageDecision(
        column="campaign",
        decision="manter",
        rationale=(
            "Numero de contatos nesta campanha para o cliente (inclui o ultimo). E uma "
            "informacao de intensidade de contato conhecida no momento da decisao do "
            "proximo passo; nao revela o resultado. Mantida como contexto."
        ),
    ),
    LeakageDecision(
        column="pdays",
        decision="manter",
        rationale=(
            "Dias desde o ultimo contato de uma campanha anterior (999 = nunca contatado). "
            "Refere-se ao passado do cliente, conhecido antes da decisao. Mantida; o "
            "sentinela 999 e documentado no dicionario de dados."
        ),
    ),
    LeakageDecision(
        column="previous",
        decision="manter",
        rationale=(
            "Numero de contatos antes desta campanha. Historico do cliente, conhecido "
            "antes da decisao. Mantida como contexto."
        ),
    ),
    LeakageDecision(
        column="poutcome",
        decision="manter",
        rationale=(
            "Resultado da campanha de marketing ANTERIOR (nao a atual). Historico "
            "conhecido antes da decisao. Mantida como contexto."
        ),
    ),
)

#: Colunas efetivamente removidas do dataset de decisao por vazamento.
LEAKAGE_COLUMNS_TO_DROP: tuple[str, ...] = tuple(
    d.column for d in LEAKAGE_DECISIONS if d.decision == "descartar"
)


@dataclass
class LoadResult:
    """Resultado de uma carga, com a proveniencia anexada para rastreabilidade."""

    raw_path: Path
    n_rows: int
    n_cols: int
    columns: list[str] = field(default_factory=list)
    source: DatasetSource = SOURCE
