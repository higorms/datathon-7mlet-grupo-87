"""Obtem o CSV bruto da base Bank Marketing.

Dois caminhos, nesta ordem de preferencia:

1. **kagglehub** - caminho oficial Kaggle (exige credencial KAGGLE_USERNAME/KAGGLE_KEY
   ou ~/.kaggle/kaggle.json). Mais fiel a referencia do desafio.
2. **UCI (fallback publico)** - baixa o zip oficial da UCI, do qual a base do Kaggle e
   um espelho. Nao exige credencial, garantindo que a banca reproduza o pipeline.

Em ambos os casos o arquivo canonico (`bank-additional-full.csv`) e copiado para
`data/kaggle/raw/`, que NAO e versionado (ver .gitignore).

Uso:
    poetry run python -m src.data.download          # baixa (kagglehub -> UCI)
    poetry run python -m src.data.download --source uci   # forca o fallback UCI
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import shutil
import zipfile
from pathlib import Path

import requests

from src.data.metadata import PROJECT_ROOT, RAW_DIR, RAW_FILENAME, SOURCE

logger = logging.getLogger(__name__)

# Timeout generoso para a rede da UCI.
_HTTP_TIMEOUT = 60


def load_env_file(path: Path | None = None) -> None:
    """Carrega pares KEY=VALUE de um arquivo .env para os.environ (sem sobrescrever).

    Carregador minimo e sem dependencia externa. Usado para que a credencial do Kaggle
    definida no .env (KAGGLE_USERNAME / KAGGLE_KEY) seja vista pelo kagglehub.
    """
    env_path = path or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def _find_csv(root: Path, filename: str) -> Path | None:
    """Procura recursivamente por `filename` dentro de `root`."""
    matches = list(root.rglob(filename))
    return matches[0] if matches else None


def _download_via_kagglehub() -> Path | None:
    """Tenta baixar pelo kagglehub. Retorna o caminho do CSV ou None se indisponivel."""
    try:
        import kagglehub  # import tardio: so e necessario neste caminho.
    except ImportError:
        logger.warning("kagglehub nao instalado; pulando caminho Kaggle.")
        return None

    try:
        logger.info("Tentando download via kagglehub: %s", SOURCE.kaggle_slug)
        path = Path(kagglehub.dataset_download(SOURCE.kaggle_slug))
    except Exception as exc:  # noqa: BLE001 - qualquer falha cai no fallback UCI.
        logger.warning("kagglehub indisponivel (%s). Usando fallback UCI.", exc)
        return None

    csv = _find_csv(path, RAW_FILENAME)
    if csv is None:
        logger.warning(
            "kagglehub baixou em %s mas %s nao foi encontrado. Fallback UCI.",
            path,
            RAW_FILENAME,
        )
        return None
    return csv


def _extract_nested_zip(archive: zipfile.ZipFile, target_name: str, out_dir: Path) -> Path | None:
    """Extrai `target_name` de um zip que pode conter zips aninhados (caso da UCI)."""
    # Caso 1: o arquivo esta diretamente no zip.
    for member in archive.namelist():
        if member.endswith(target_name):
            archive.extract(member, out_dir)
            return out_dir / member

    # Caso 2: esta dentro de um zip aninhado (ex.: bank-additional.zip).
    for member in archive.namelist():
        if member.endswith(".zip"):
            with archive.open(member) as nested_bytes:
                with zipfile.ZipFile(io.BytesIO(nested_bytes.read())) as nested:
                    found = _extract_nested_zip(nested, target_name, out_dir)
                    if found is not None:
                        return found
    return None


def _download_via_uci() -> Path:
    """Baixa o zip da UCI e extrai o CSV canonico. Levanta erro se falhar."""
    logger.info("Baixando da UCI: %s", SOURCE.uci_download_url)
    resp = requests.get(SOURCE.uci_download_url, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()

    extract_dir = RAW_DIR / "_uci_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv = _extract_nested_zip(zf, RAW_FILENAME, extract_dir)

    if csv is None:
        raise FileNotFoundError(
            f"{RAW_FILENAME} nao encontrado no zip da UCI ({SOURCE.uci_download_url})."
        )
    return csv


def download_raw(source: str = "auto", force: bool = False) -> Path:
    """Garante `data/kaggle/raw/bank-additional-full.csv` localmente e retorna seu caminho.

    Args:
        source: "auto" (kagglehub -> UCI), "kaggle" (so kagglehub) ou "uci" (so UCI).
        force: se True, baixa novamente mesmo que o arquivo ja exista.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / RAW_FILENAME

    if dest.exists() and not force:
        logger.info("Arquivo bruto ja existe: %s (use --force para rebaixar).", dest)
        return dest

    # Disponibiliza credenciais do .env (KAGGLE_USERNAME / KAGGLE_KEY) ao kagglehub.
    load_env_file()

    csv_path: Path | None = None
    if source in ("auto", "kaggle"):
        csv_path = _download_via_kagglehub()
    if csv_path is None and source in ("auto", "uci"):
        csv_path = _download_via_uci()
    if csv_path is None:
        raise RuntimeError(
            "Nao foi possivel obter a base por nenhum caminho. "
            "Configure a credencial Kaggle ou verifique o acesso a internet (UCI)."
        )

    shutil.copyfile(csv_path, dest)
    # Limpa diretorio temporario de extracao da UCI, se houver.
    tmp = RAW_DIR / "_uci_extract"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)

    size_kb = dest.stat().st_size / 1024
    logger.info("CSV bruto disponivel em %s (%.1f KB).", dest, size_kb)
    return dest


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Baixa a base bruta Bank Marketing.")
    parser.add_argument(
        "--source",
        choices=["auto", "kaggle", "uci"],
        default="auto",
        help="Caminho de download (default: auto = kagglehub e, se falhar, UCI).",
    )
    parser.add_argument("--force", action="store_true", help="Rebaixa mesmo se ja existir.")
    args = parser.parse_args()
    path = download_raw(source=args.source, force=args.force)
    print(path)


if __name__ == "__main__":
    main()
