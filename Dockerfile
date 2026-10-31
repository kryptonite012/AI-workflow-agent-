# Dockerfile for AI-Agent-Workflow
# Requires the application source in ./src (entry point: src/main_orchestrator.py).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies from the lockfile first so this layer is cached between code changes
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project --no-dev

COPY src/ ./src

# Run as an unprivileged user
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "src/main_orchestrator.py"]
