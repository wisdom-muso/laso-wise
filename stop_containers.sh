#!/bin/bash

# This script stops any existing containers before starting new ones

echo "Checking for existing containers..."

# Check if any containers are running with the project name
if docker compose -f docker-compose.prod.yml ps -q | grep -q .; then
    echo "Stopping existing containers..."
    docker compose -f docker-compose.prod.yml down
    echo "Existing containers stopped."
else
    echo "No existing containers found."
fi

# Check if port 8080 is in use
if netstat -tuln | grep -q ":8080"; then
    echo "Warning: Port 8080 is already in use."
    echo "Please make sure no other service is using port 8080 before continuing."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

echo "Ready to start new containers."