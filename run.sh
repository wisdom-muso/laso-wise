#!/bin/bash

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is not installed. Please install it first."
    exit 1
fi

# Check if .env file exists, if not create it from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration."
fi

# Build and run the application
echo "Building and starting the application..."
docker-compose up --build

# Exit message
echo "Application stopped."