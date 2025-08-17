#!/bin/bash

echo "=== Fixing Port Conflicts and Updating Configuration ==="

# Stop all running containers
echo "[INFO] Stopping all Docker containers..."
docker compose -f docker-compose.prod.yml down --remove-orphans

# Remove any containers using port 80
echo "[INFO] Checking for containers using port 80..."
CONTAINERS_ON_80=$(docker ps --filter "publish=80" -q)
if [ ! -z "$CONTAINERS_ON_80" ]; then
    echo "[INFO] Stopping containers using port 80..."
    docker stop $CONTAINERS_ON_80
    docker rm $CONTAINERS_ON_80
fi

# Clean up any dangling containers
echo "[INFO] Cleaning up dangling containers..."
docker container prune -f

# Show what's using port 80
echo "[INFO] Current processes using port 80:"
sudo lsof -i :80 || echo "No processes found using port 80"

echo "[INFO] Current processes using port 3000:"
sudo lsof -i :3000 || echo "No processes found using port 3000"

echo "[SUCCESS] Port conflict cleanup completed!"
echo "[INFO] You can now run: ./deploy.sh"