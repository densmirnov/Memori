FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy repository (Memori core + gateway)
COPY . /app

# Install dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r memori-gateway/requirements.txt

WORKDIR /app/memori-gateway

ENV HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "app", "http"]
