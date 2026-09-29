# ---- builder ----
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir --prefix=/install .

# ---- runtime ----
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts

ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/storage/documents /app/.cache/huggingface && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8013/health/live', timeout=3).raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8013", "--workers", "4"]