#!/bin/bash

# Enhanced script for collecting static files and handling duplicates
# This script provides a more comprehensive solution to the static files duplication issue

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    echo "No .env file found, using default environment variables."
fi

# Create necessary directories if they don't exist
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# Log file for the static collection process
LOG_FILE="logs/static_collection_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

echo "Starting static files collection process..." | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"

# Function to safely remove files/directories and log the action
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "  - Removing $path" | tee -a "$LOG_FILE"
        rm -rf "$path"
        return 0
    else
        echo "  - $path not found, skipping" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Step 1: Remove all potential duplicate static files
echo "Removing potential duplicate static files..." | tee -a "$LOG_FILE"

# CKEditor files
echo "Handling CKEditor files..." | tee -a "$LOG_FILE"
safe_remove "static/ckeditor/ckeditor"
safe_remove "static/ckeditor/file-icons"
safe_remove "static/ckeditor/galleriffic"
safe_remove "static/ckeditor/ckeditor-init.js"
safe_remove "static/ckeditor/ckeditor.css"
safe_remove "static/ckeditor/fixups.js"

# Django Unfold files
echo "Handling Django Unfold files..." | tee -a "$LOG_FILE"
safe_remove "static/unfold"

# Django Admin files
echo "Handling Django Admin files..." | tee -a "$LOG_FILE"
safe_remove "static/admin"

# Django REST Framework files
echo "Handling Django REST Framework files..." | tee -a "$LOG_FILE"
safe_remove "static/rest_framework"

# Debug Toolbar files
echo "Handling Debug Toolbar files..." | tee -a "$LOG_FILE"
safe_remove "static/debug_toolbar"

# Step 2: Clear existing static files
echo "Clearing existing static files..." | tee -a "$LOG_FILE"
if [ -d "staticfiles" ]; then
    find staticfiles -type f -not -path "*/\.*" -delete
    echo "  - Existing static files cleared" | tee -a "$LOG_FILE"
else
    echo "  - No staticfiles directory found" | tee -a "$LOG_FILE"
fi

# Step 3: Collect static files
echo "Collecting static files..." | tee -a "$LOG_FILE"
python3 manage.py collectstatic --noinput --clear --verbosity 1 2>&1 | tee -a "$LOG_FILE"

# Step 4: Check for any warnings or errors in the log
if grep -q "Found another file with the destination path" "$LOG_FILE"; then
    echo "WARNING: Some duplicate files were found during collection." | tee -a "$LOG_FILE"
    echo "These are expected and were handled by Django's collectstatic." | tee -a "$LOG_FILE"
fi

# Step 5: Set proper permissions
echo "Setting proper permissions on static files..." | tee -a "$LOG_FILE"
find staticfiles -type d -exec chmod 755 {} \;
find staticfiles -type f -exec chmod 644 {} \;

echo "Static files collection completed successfully." | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE"