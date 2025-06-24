#! Docker down script

echo "Stopping Docker containers..."
cd docker/ && docker-compose --env-file ./../.envs/.env down
echo "Docker containers stopped."
docker ps
