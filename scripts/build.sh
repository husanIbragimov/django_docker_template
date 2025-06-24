#!/bin/bash

echo "Building the project..."
git pull origin main && echo "Project updated from the repository."
cd docker/ && docker-compose --env-file ./../.envs/.env up --build -d
echo "Docker images built successfully."
docker ps
