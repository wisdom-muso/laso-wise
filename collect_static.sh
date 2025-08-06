#!/bin/bash

# This script collects static files separately from the Docker build process

# Load environment variables
set -a
source .env
set +a

# Create directories if they don't exist
mkdir -p staticfiles
mkdir -p media

# Clear existing static files
echo "Clearing existing static files..."
rm -rf staticfiles/*

# Collect static files with minimal output
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity 0

echo "Static files collection completed."