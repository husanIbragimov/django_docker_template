#!/bin/bash
# Dev: full stack (web, celery, postgres, redis) + nginx serving static/media on http://localhost:8000
set -e
"$(dirname "$0")/compose.sh" dev up --build -d --remove-orphans
docker ps --format "{{.Names}}" | sort
