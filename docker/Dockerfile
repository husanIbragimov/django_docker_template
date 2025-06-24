FROM python:3.12-slim

# Env variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SLAB_DEV=prod

# OS packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY ./../requirements/base.txt ./
COPY ./../requirements/production.txt ./
RUN pip install --upgrade pip && pip install -r production.txt

# App code
WORKDIR /app/src
COPY ./../src ./src
COPY ../.envs/.env /app/.envs/.env
