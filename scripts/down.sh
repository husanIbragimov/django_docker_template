#!/bin/bash
# Stop containers: bash scripts/down.sh [dev|prod|local]  (default: dev)
set -e
echo "Stopping Docker containers..."
"$(dirname "$0")/compose.sh" "${1:-dev}" down
echo "Docker containers stopped."
docker ps
