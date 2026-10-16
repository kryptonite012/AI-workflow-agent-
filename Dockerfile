# Dockerfile for AI-Agent-Workflow
FROM python:3.13-slim

# Node.js is needed to launch MCP servers via `npx` (see .mcp.json)
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # No GUI inside the container: keep the log server in the background
    LOG_DISPLAY_MODE=file \
    ENABLE_SOUND_NOTIFICATIONS=false

# Install dependencies first so they are cached between source changes
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src
RUN mkdir -p basic_logs

CMD ["python", "src/main_orchestrator.py"]
