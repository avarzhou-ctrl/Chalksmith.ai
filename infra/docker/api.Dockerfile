FROM ghcr.io/astral-sh/uv:0.9.30 AS uv
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/chalksmith
COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock backend/
RUN uv sync --project backend --frozen --no-dev --no-extra video
COPY backend backend

ENV PATH="/srv/chalksmith/backend/.venv/bin:$PATH"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
