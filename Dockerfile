# Imagem de producao do servico de decisao (Etapa 5/6).
# Build:  docker build -t datathon-decision-api .
# Run:    docker run -p 8000:8000 datathon-decision-api

FROM python:3.12-slim AS builder

ENV POETRY_VERSION=2.1.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY src/ ./src/
COPY data/synthetic_enrichment/offer_catalog.parquet ./data/synthetic_enrichment/offer_catalog.parquet

# ---------------------------------------------------------------------------

FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src ./src
COPY --from=builder /app/data ./data

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
