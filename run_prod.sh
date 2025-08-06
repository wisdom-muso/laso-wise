#!/bin/bash

# Check if docker compose is installed
if ! command -v docker &> /dev/null; then
    echo "docker is not installed. Please install it first."
    exit 1
fi

# Check if .env file exists, if not create it from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration."
fi

# Stop any existing containers
echo "Checking for existing containers..."
./stop_containers.sh

# Collect static files separately
echo "Collecting static files..."
./collect_static.sh

# Build and run the application in production mode
echo "Building and starting the application in production mode..."
docker compose -f docker-compose.prod.yml up --build -d

# Show running containers
echo "Running containers:"
docker compose -f docker-compose.prod.yml ps

echo "Application started in production mode."
echo "Access the application at http://localhost:8080"