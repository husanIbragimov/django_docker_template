#!/bin/bash
# Local: only postgres + redis in Docker; run Django and Celery by hand on the host.
# Connection settings for the host come from .envs/.env.local (localhost:5439 / localhost:6379).
set -e
"$(dirname "$0")/compose.sh" local up -d --remove-orphans
cat <<'MSG'
postgres -> localhost:5439, redis -> localhost:6379

Now run in separate terminals (from the repo root, with your venv active):
  python src/manage.py migrate
  python src/manage.py runserver
  cd src && celery -A config worker --loglevel=INFO
MSG
