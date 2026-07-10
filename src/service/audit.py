"""Log auditavel append-only das decisoes (Etapa 5).

Cada decisao vira uma linha JSON em `logs/decisions.jsonl` contendo a resposta completa
(braco, reason codes, versao da politica, decision_id) e o contexto de entrada, permitindo
reconstruir e auditar qualquer decisao. O diretorio `logs/` nao e versionado.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.data.metadata import PROJECT_ROOT

#: Caminho padrao do log auditavel (sobrescrevivel por AUDIT_LOG_PATH ou parametro).
DEFAULT_AUDIT_PATH = PROJECT_ROOT / "logs" / "decisions.jsonl"


def _resolve_path(path: str | Path | None) -> Path:
    if path is not None:
        return Path(path)
    env = os.environ.get("AUDIT_LOG_PATH")
    return Path(env) if env else DEFAULT_AUDIT_PATH


def write_audit_record(
    response: dict[str, Any],
    context: dict[str, Any],
    path: str | Path | None = None,
) -> Path:
    """Anexa um registro de decisao ao log auditavel. Retorna o caminho usado."""
    audit_path = _resolve_path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {**response, "context": context}
    with open(audit_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return audit_path


def read_audit_record(
    decision_id: str,
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Recupera o registro de uma decisao pelo decision_id (ou None se nao achar)."""
    audit_path = _resolve_path(path)
    if not audit_path.exists():
        return None
    with open(audit_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("decision_id") == decision_id:
                return record
    return None
