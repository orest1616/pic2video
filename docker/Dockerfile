# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
RUN pip install --upgrade pip && \
    pip install .


FROM python:3.11-slim AS runtime
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed site-packages from builder
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Copy application
COPY app /app/app
COPY web /app/web

# Create data dir
RUN mkdir -p /app/data/input /app/data/output /app/data/jobs && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    MORPH_WORK_DIR=/app/data \
    MAX_UPLOAD_IMAGES=10 \
    MAX_IMAGE_SIZE_MB=25 \
    ALLOWED_IMAGE_TYPES="image/jpeg,image/png"

# Use APP_PORT env var at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}"]
