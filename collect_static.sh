#!/bin/bash

# This script collects static files separately from the Docker build process

# Load environment variables
set -a
source .env
set +a

# Create directories if they don't exist
mkdir -p staticfiles
mkdir -p media

# Remove duplicate static files to prevent conflicts
echo "Removing duplicate static files..."

# 1. Remove duplicate CKEditor files
if [ -d "static/ckeditor/ckeditor" ]; then
    echo "  - Removing static/ckeditor/ckeditor"
    rm -rf static/ckeditor/ckeditor
fi

# 2. Remove duplicate CKEditor support files
if [ -d "static/ckeditor/file-icons" ]; then
    echo "  - Removing static/ckeditor/file-icons"
    rm -rf static/ckeditor/file-icons
fi

if [ -d "static/ckeditor/galleriffic" ]; then
    echo "  - Removing static/ckeditor/galleriffic"
    rm -rf static/ckeditor/galleriffic
fi

# 3. Remove specific CKEditor files that cause conflicts
if [ -f "static/ckeditor/ckeditor-init.js" ]; then
    echo "  - Removing static/ckeditor/ckeditor-init.js"
    rm -f static/ckeditor/ckeditor-init.js
fi

if [ -f "static/ckeditor/ckeditor.css" ]; then
    echo "  - Removing static/ckeditor/ckeditor.css"
    rm -f static/ckeditor/ckeditor.css
fi

if [ -f "static/ckeditor/fixups.js" ]; then
    echo "  - Removing static/ckeditor/fixups.js"
    rm -f static/ckeditor/fixups.js
fi

# 4. Remove duplicate Unfold files
if [ -d "static/unfold" ]; then
    echo "  - Removing static/unfold"
    rm -rf static/unfold
fi

# 5. Remove duplicate admin files
if [ -d "static/admin" ]; then
    echo "  - Removing static/admin"
    rm -rf static/admin
fi

# Clear existing static files
echo "Clearing existing static files..."
rm -rf staticfiles/*

# Collect static files with minimal output
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity 0

echo "Static files collection completed."