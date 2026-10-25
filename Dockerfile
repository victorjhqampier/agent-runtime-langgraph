FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /axapp

COPY --from=ghcr.io/astral-sh/uv:0.11.18 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/

EXPOSE 80

CMD ["/axapp/.venv/bin/uvicorn", "Presentation.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "80", "--workers", "1", "--loop", "uvloop", "--http", "httptools"]
