#!/bin/bash
# Shared docker compose wrapper: scripts/compose.sh <dev|prod|local> <compose args...>
set -e
ENV_NAME="$1"; shift || true
usage() {
  cat <<MSG
Usage: $0 <dev|prod|local> <docker compose command...>
  e.g. $0 dev up --build -d
       $0 dev logs -f web
       $0 prod ps
To just start a stack use: bash scripts/run_dev.sh | run_prod.sh | run_local.sh
MSG
  exit 1
}
case "$ENV_NAME" in
  dev|prod|local) ;;
  *) usage ;;
esac
[ $# -eq 0 ] && usage
cd "$(dirname "$0")/../docker"
exec docker compose -f "docker-compose.$ENV_NAME.yml" --env-file ../.envs/.env "$@"
