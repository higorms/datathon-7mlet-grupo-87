"""Metadados da politica servida: versao e hash do catalogo (rastreabilidade).

`POLICY_VERSION` identifica a versao logica da politica de decisao (habilita promocao/
rollback na Etapa 7). `catalog_hash()` fixa qual catalogo de ofertas (Etapa 2) esta em uso.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

from src.bandits.environment import SYNTH_DIR

#: Versao logica da politica de decisao (contextual gulosa + trilhos de seguranca).
POLICY_VERSION = "context-greedy-v1"


@lru_cache(maxsize=1)
def catalog_hash() -> str:
    """SHA-256 (12 primeiros hex) do catalogo de ofertas em uso."""
    path = SYNTH_DIR / "offer_catalog.parquet"
    if not path.exists():
        return "unknown"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
