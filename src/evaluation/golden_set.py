"""Carregamento e validacao do golden set."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.data.metadata import PROJECT_ROOT
from src.evaluation.schema import GoldenCase

DEFAULT_GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "golden_set" / "evaluation_cases.jsonl"


def load_golden_cases(path: Path | None = None) -> list[GoldenCase]:
    """Carrega e valida todos os casos do JSONL."""
    golden_path = path or DEFAULT_GOLDEN_SET_PATH
    if not golden_path.exists():
        raise FileNotFoundError(f"Golden set ausente: {golden_path}")

    cases: list[GoldenCase] = []
    with golden_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                cases.append(GoldenCase.model_validate(payload))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Linha {line_no} invalida em {golden_path}: {exc}") from exc

    if len(cases) < 20:
        raise ValueError(f"Golden set precisa de >= 20 casos; encontrados {len(cases)}.")
    return cases


def coverage_summary(cases: list[GoldenCase]) -> dict[str, int]:
    """Contagem de casos por categoria."""
    return dict(Counter(c.category for c in cases))
