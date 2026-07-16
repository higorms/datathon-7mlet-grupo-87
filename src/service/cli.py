"""Decisao one-shot por linha de comando, sem subir o servidor (Etapa 5).

Uso:
    poetry run python -m src.service.cli --context '{"age": 22, "contact": "cellular"}'
    poetry run python -m src.service.cli --context-file contexto.json
"""

from __future__ import annotations

import argparse
import json
import sys

from pydantic import ValidationError

from src.service.contracts import DecisionRequest
from src.service.decision import make_decision


def main() -> None:
    parser = argparse.ArgumentParser(description="Decisao one-shot do servico (Etapa 5).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--context", type=str, help="Contexto de decisao em JSON (string).")
    group.add_argument("--context-file", type=str, help="Arquivo JSON com o contexto.")
    parser.add_argument("--no-audit", action="store_true", help="Nao gravar no log auditavel.")
    args = parser.parse_args()

    raw = args.context if args.context else open(args.context_file, encoding="utf-8").read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERRO: JSON invalido: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    try:
        request = DecisionRequest(**payload)
    except ValidationError as exc:
        print(f"ERRO: contexto invalido:\n{exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    response = make_decision(request, write_audit=not args.no_audit)
    print(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
