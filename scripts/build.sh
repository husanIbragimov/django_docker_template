#!/bin/bash
# Deploy: pull latest code and rebuild the prod stack
set -e
cd "$(dirname "$0")/.."
echo "Building the project..."
git pull origin main && echo "Project updated from the repository."
bash scripts/run_prod.sh
echo "Remove none images from computer"
docker images -f "dangling=true" -q | xargs -r docker rmi -f
