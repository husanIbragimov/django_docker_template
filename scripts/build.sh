#!/bin/bash

echo "Building the project..."
git pull origin main && echo "Project updated from the repository."
cd docker/ && docker-compose --env-file ./../.envs/.env up --build -d
echo "Remove none images from computer"
docker rmi -f $(docker images | grep "<none>" | awk "{print \$3}")
echo "Containers running:"
docker ps --format "{{.Names}}" | sort
