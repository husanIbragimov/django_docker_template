# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

# Env variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TEMPLATE_DEV=prod

# OS packages (apt cache is kept between builds via BuildKit cache mounts)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update && apt-get install -y --no-install-recommends netcat-openbsd

WORKDIR /app

# Python dependencies — this layer is rebuilt only when requirements change,
# and downloaded wheels are reused from the pip cache mount
COPY requirements/base.txt requirements/production.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r production.txt

# App code (bind-mounted over in docker-compose, copied here for standalone runs)
WORKDIR /app/src
COPY src/ ./
