FROM ghcr.io/astral-sh/uv:0.9.30 AS uv
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        dvisvgm \
        ffmpeg \
        fonts-inter \
        fonts-noto-cjk \
        libcairo2-dev \
        libpango1.0-dev \
        pkg-config \
        texlive-fonts-recommended \
        texlive-latex-base \
        texlive-latex-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/chalksmith
COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock backend/
RUN uv sync --project backend --frozen --no-dev --extra video
COPY backend backend

ENV APP_ROLE=renderer PATH="/srv/chalksmith/backend/.venv/bin:$PATH"
CMD ["uvicorn", "backend.app.renderer_main:renderer_app", "--host", "0.0.0.0", "--port", "8080"]
