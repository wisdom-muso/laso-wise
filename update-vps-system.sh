#!/bin/bash

# LASO Healthcare System - VPS Update Script
# This script updates your VPS to the latest version of the system

set -e

echo "🔄 LASO Healthcare - VPS System Update"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "Starting VPS system update..."

# Step 1: Check current status
log_info "Checking current system status..."
echo "Current directory: $(pwd)"
echo "Current branch: $(git branch --show-current 2>/dev/null || echo 'Unknown')"
echo "Last commit: $(git log -1 --oneline 2>/dev/null || echo 'Unknown')"
echo ""

# Step 2: Stop any running Django processes
log_info "Stopping any running Django processes..."
pkill -f "python.*manage.py.*runserver" || true
pkill -f "gunicorn.*laso" || true
sleep 2
log_success "Stopped running processes"

# Step 3: Backup current state
log_info "Creating backup of current state..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
    log_success "Database backed up"
fi

# Step 4: Fetch latest changes
log_info "Fetching latest changes from repository..."
git fetch origin
git status

# Step 5: Check if we're on the right branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "master" ] && [ "$CURRENT_BRANCH" != "main" ]; then
    log_warning "You're on branch '$CURRENT_BRANCH'. Switching to master..."
    git checkout master
    git pull origin master
else
    log_info "Pulling latest changes..."
    git pull origin $CURRENT_BRANCH
fi

# Step 6: Show what changed
log_info "Recent changes:"
git log --oneline -5
echo ""

# Step 7: Update Python dependencies
log_info "Updating Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Dependencies updated"
else
    log_error "Virtual environment not found. Please run the setup script first."
    exit 1
fi

# Step 8: Load environment variables
log_info "Loading environment variables..."
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    log_success "Environment variables loaded"
else
    log_error ".env file not found"
    exit 1
fi

# Step 9: Run migrations
log_info "Running database migrations..."
python manage.py makemigrations
python manage.py migrate
log_success "Migrations completed"

# Step 10: Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput
log_success "Static files collected"

# Step 11: Clear any Django cache
log_info "Clearing Django cache..."
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared')
" 2>/dev/null || true

# Step 12: Check for template changes
log_info "Checking template files..."
if [ -f "users/templates/users/patient_registration.html" ]; then
    if grep -q "blood_type" users/templates/users/patient_registration.html; then
        log_success "✅ Blood type field found in registration template"
    else
        log_error "❌ Blood type field NOT found in registration template"
    fi
    
    if grep -q "address" users/templates/users/patient_registration.html; then
        log_success "✅ Address field found in registration template"
    else
        log_error "❌ Address field NOT found in registration template"
    fi
else
    log_error "Registration template not found"
fi

# Step 13: Test the system
log_info "Testing system functionality..."
python manage.py check
log_success "System check passed"

# Step 14: Show current version info
log_info "Current system version:"
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git log -1 --oneline)"
echo "Date: $(git log -1 --format='%cd')"
echo ""

# Step 15: Instructions for restarting
echo "🎉 System Update Complete!"
echo "========================="
echo ""
echo "Next steps:"
echo "1. Start your Django server:"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "2. Or if using Gunicorn:"
echo "   gunicorn --bind 0.0.0.0:8000 laso_healthcare.wsgi:application"
echo ""
echo "3. Access your system at:"
echo "   http://your-vps-ip:8000"
echo ""
echo "4. Check the signup page should now have:"
echo "   ✅ Blood type dropdown"
echo "   ✅ Address textarea"
echo "   ✅ Date of birth picker"
echo "   ✅ Gender dropdown"
echo ""

log_success "VPS update completed successfully!"