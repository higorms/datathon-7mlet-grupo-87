"""Pipeline ponta a ponta local (Etapa 5).

Reproduz a cadeia da solucao em um comando: garante os dados processados (Etapa 1),
confirma a camada sintetica (Etapa 2) e demonstra o servico de decisao (Etapa 5) com
dois exemplos (caso tipico e trilho de seguranca), gravando a auditoria.

Uso:
    poetry run python scripts/run_pipeline.py
Depois, para subir a API:
    poetry run uvicorn src.service.app:app --reload
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Permite rodar como script solto (`python scripts/run_pipeline.py`): garante a raiz no path.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.bandits.environment import SYNTH_DIR  # noqa: E402
from src.data.build_processed import load_processed  # noqa: E402
from src.service.contracts import DecisionRequest  # noqa: E402
from src.service.decision import make_decision  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("run_pipeline")

DEMOS = [
    (
        "Caso tipico (jovem + celular + sucesso)",
        {"age": 22, "contact": "cellular", "poutcome": "success", "pdays": 180,
         "job": "student", "month": "oct", "segment_macro_regime": "tight"},
    ),
    (
        "Trilho de seguranca (canal invalido)",
        {"age": 40, "contact": "email"},
    ),
    (
        "Incentivo bloqueado (redireciona rate_boost)",
        {"age": 30, "contact": "cellular", "poutcome": "success",
         "financial_incentive_blocked": True},
    ),
]


def main() -> None:
    log.info("[1/3] Garantindo dados processados (Etapa 1)...")
    df = load_processed()
    log.info("      processado: %d linhas x %d colunas", df.shape[0], df.shape[1])

    log.info("[2/3] Conferindo camada sintetica (Etapa 2)...")
    catalog = SYNTH_DIR / "offer_catalog.parquet"
    if not catalog.exists():
        raise FileNotFoundError(
            f"{catalog} ausente. Gere a Etapa 2 (notebooks/02_enriquecimento_sintetico.ipynb)."
        )
    log.info("      catalogo presente: %s", catalog.name)

    log.info("[3/3] Demonstrando o servico de decisao (Etapa 5)...")
    for title, ctx in DEMOS:
        resp = make_decision(DecisionRequest(**ctx))
        print(f"\n>>> {title}")
        print(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2))

    print("\n=== Pipeline concluido ===")
    print("Auditoria gravada em logs/decisions.jsonl")
    print("Para subir a API:   poetry run uvicorn src.service.app:app --reload")
    print("Contrato interativo: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main()
