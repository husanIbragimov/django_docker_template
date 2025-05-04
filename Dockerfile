FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV SANOQ_DEV prod

RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean

WORKDIR /app
COPY requirements/base.txt .
COPY requirements/production.txt .
RUN pip install -r production.txt
WORKDIR /app/src
COPY src /app/src
COPY .envs /app/.envs
