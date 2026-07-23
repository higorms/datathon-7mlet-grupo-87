"""Registro de politicas com versionamento e estagios (Etapa 7).

Mantem, por politica, o estagio atual (dev -> staging -> prod -> archived), as metricas
que embasaram a promocao e um historico de transicoes. Suporta **rollback** (voltar o
estagio para a politica anterior). Persistido em JSON versionavel.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.metadata import PROJECT_ROOT

REGISTRY_PATH = PROJECT_ROOT / "mlops" / "policy_registry.json"

#: Ordem dos estagios promoviveis.
STAGE_ORDER = ("dev", "staging", "prod")
STAGES = (*STAGE_ORDER, "archived")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class PolicyRegistry:
    """Registro de politicas (carrega/salva JSON e opera estagios)."""

    def __init__(self, data: dict[str, Any] | None = None, path: Path | None = None) -> None:
        self.path = Path(path) if path else REGISTRY_PATH
        self.data: dict[str, Any] = data or {"policies": {}, "active": {s: None for s in STAGE_ORDER}}

    # ------------------------------------------------------------------ IO
    @classmethod
    def load(cls, path: Path | None = None) -> PolicyRegistry:
        p = Path(path) if path else REGISTRY_PATH
        if p.exists():
            return cls(json.loads(p.read_text(encoding="utf-8")), path=p)
        return cls(path=p)

    def save(self, path: Path | None = None) -> Path:
        out = Path(path) if path else self.path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return out

    # -------------------------------------------------------------- queries
    def get(self, version: str) -> dict[str, Any] | None:
        return self.data["policies"].get(version)

    def active(self, stage: str) -> str | None:
        return self.data["active"].get(stage)

    def list_policies(self) -> list[dict[str, Any]]:
        return list(self.data["policies"].values())

    # --------------------------------------------------------------- writes
    def register(
        self,
        version: str,
        metrics: dict[str, Any],
        description: str = "",
        stage: str = "dev",
        actor: str = "system",
    ) -> dict[str, Any]:
        """Registra uma nova politica (ou atualiza metricas se ja existir) no estagio dado."""
        if stage not in STAGES:
            raise ValueError(f"estagio invalido: {stage}")
        entry = self.data["policies"].get(version, {
            "version": version,
            "created_at": _now(),
            "history": [],
        })
        entry.update({"stage": stage, "metrics": metrics, "description": description})
        entry["history"].append(
            {"ts": _now(), "event": "register", "to_stage": stage, "actor": actor}
        )
        self.data["policies"][version] = entry
        if stage in STAGE_ORDER:
            self.data["active"][stage] = version
        return entry

    def promote(self, version: str, to_stage: str, actor: str, note: str = "") -> dict[str, Any]:
        """Promove uma politica para o proximo estagio (dev->staging->prod)."""
        entry = self.data["policies"].get(version)
        if entry is None:
            raise KeyError(f"politica desconhecida: {version}")
        if to_stage not in STAGE_ORDER:
            raise ValueError(f"estagio de promocao invalido: {to_stage}")

        current = entry["stage"]
        if current in STAGE_ORDER:
            expected_idx = STAGE_ORDER.index(current) + 1
            if expected_idx >= len(STAGE_ORDER) or STAGE_ORDER[expected_idx] != to_stage:
                raise ValueError(
                    f"transicao invalida {current} -> {to_stage} (esperado sequencial)."
                )

        entry["stage"] = to_stage
        entry["history"].append(
            {"ts": _now(), "event": "promote", "from_stage": current,
             "to_stage": to_stage, "actor": actor, "note": note}
        )
        self.data["active"][to_stage] = version
        return entry

    def rollback(self, stage: str, actor: str, note: str = "") -> str | None:
        """Reverte o estagio para a politica ativa anterior (rollback controlado)."""
        if stage not in STAGE_ORDER:
            raise ValueError(f"estagio invalido: {stage}")
        current = self.data["active"].get(stage)
        # Procura, no historico, a versao anterior que esteve ativa neste estagio.
        promoted_here = [
            h_version
            for h_version, entry in self.data["policies"].items()
            for h in entry["history"]
            if h.get("to_stage") == stage
        ]
        # Mantem a ordem cronologica pelo ts do ultimo evento de promocao para o estagio.
        def _last_ts(v: str) -> str:
            evs = [h["ts"] for h in self.data["policies"][v]["history"] if h.get("to_stage") == stage]
            return max(evs) if evs else ""

        ordered = sorted(set(promoted_here), key=_last_ts)
        previous = None
        for v in reversed(ordered):
            if v != current:
                previous = v
                break
        if previous is None:
            return None

        self.data["active"][stage] = previous
        self.data["policies"][previous]["stage"] = stage
        if current is not None:
            self.data["policies"][current]["stage"] = "archived"
        self.data["policies"][previous]["history"].append(
            {"ts": _now(), "event": "rollback", "to_stage": stage,
             "from_version": current, "actor": actor, "note": note}
        )
        return previous
