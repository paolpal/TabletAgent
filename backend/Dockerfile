FROM ghcr.io/astral-sh/uv:0.9.13 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project && useradd --create-home appuser && mkdir /data && chown appuser:appuser /data
COPY app ./app
COPY asgi.py .
USER appuser
CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8000"]
