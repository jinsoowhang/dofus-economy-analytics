FROM ghcr.io/astral-sh/uv:0.12.0 AS uv
FROM python:3.12-slim-bookworm

COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DOFUS_PROJECT_ROOT=/app PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN uv sync --locked --no-dev --no-editable \
    && mkdir -p data/app \
    && chown -R 10001:10001 data
USER 10001:10001
CMD ["uvicorn", "dofus_touch_economy.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--no-access-log"]
