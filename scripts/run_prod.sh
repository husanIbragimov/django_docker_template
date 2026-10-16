#!/bin/bash
# Prod: full stack (web, celery, postgres, redis), no nginx
set -e
"$(dirname "$0")/compose.sh" prod up --build -d --remove-orphans
docker ps --format "{{.Names}}" | sort
