"""Testes de governança (Etapa 8): valida presença das seções obrigatórias nos documentos."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GOVERNANCE_DOCS = {
    "docs/model-card.md": [
        "## 4. Intended use",
        "## 5. Out-of-scope",
        "## 6. Análise de fairness",
        "## 7. Vieses conhecidos",
        "## 8. Limitações técnicas",
        "## 9. Plano de revisão periódica",
        "context-greedy-v1",
        "Thompson Sampling",
    ],
    "docs/system-card.md": [
        "## 5. Cenários de risco",
        "Reward hacking",
        "Manipulação do contexto",
        "Abuso do assistente",
        "Violação de suitability",
        "## 6. Plano de monitoramento",
        "SAFE_FALLBACK",
    ],
    "docs/lgpd-plan.md": [
        "## 2. Base legal e finalidade",
        "## 3. Minimização de dados",
        "## 4. Ciclo de retenção",
        "## 5. Mapeamento de identificadores",
        "## 6. Política de logs e telemetria",
        "## 7. Plano de resposta a incidentes",
    ],
    "reports/technical-report.md": [
        "## 1. Problema e motivação",
        "## 4. Modelagem como multi-armed bandit",
        "## 6. Arquitetura-alvo Azure",
        "## 7. Ciclo de vida MLOps",
        "## 8. Governança",
        "## 10. Trabalhos futuros",
    ],
}

PITCH_DOCS = {
    "docs/pitch/slides.md": [
        "Thompson Sampling",
        "FinOps",
        "context-greedy-v1",
    ],
    "docs/pitch/roteiro.md": [
        "10 minutos",
        "FAQ antecipado",
        "FinOps",
    ],
    "docs/demo-plan.md": [
        "Plano de contingência",
        "GS-T01",
        "GS-A03",
        "GS-A04",
    ],
}


@pytest.mark.parametrize("rel_path,required_sections", list(GOVERNANCE_DOCS.items()))
def test_governance_doc_sections(rel_path: str, required_sections: list[str]) -> None:
    path = PROJECT_ROOT / rel_path
    assert path.exists(), f"Documento obrigatório ausente: {rel_path}"
    content = path.read_text(encoding="utf-8")
    for section in required_sections:
        assert section in content, f"Seção '{section}' ausente em {rel_path}"


@pytest.mark.parametrize("rel_path,required_sections", list(PITCH_DOCS.items()))
def test_pitch_doc_sections(rel_path: str, required_sections: list[str]) -> None:
    path = PROJECT_ROOT / rel_path
    assert path.exists(), f"Documento de pitch ausente: {rel_path}"
    content = path.read_text(encoding="utf-8")
    for section in required_sections:
        assert section in content, f"Seção '{section}' ausente em {rel_path}"


def test_model_card_references_real_metrics() -> None:
    content = (PROJECT_ROOT / "docs/model-card.md").read_text(encoding="utf-8")
    assert "56.6" in content
    assert "100%" in content or "100.0%" in content or "24/24" in content


def test_technical_report_within_reasonable_length() -> None:
    content = (PROJECT_ROOT / "reports/technical-report.md").read_text(encoding="utf-8")
    word_count = len(content.split())
    assert word_count < 6000, f"Relatório técnico muito longo: {word_count} palavras (máx ~5000)"
