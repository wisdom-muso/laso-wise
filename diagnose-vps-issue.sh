#!/bin/bash

# LASO Healthcare System - VPS Diagnostic Script
# This script helps diagnose why your VPS is showing old version

echo "🔍 LASO Healthcare - VPS Diagnostic"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running diagnostic from: $(pwd)"
echo ""

# 1. Check Git status
log_info "1. Checking Git repository status..."
if [ -d ".git" ]; then
    echo "Current branch: $(git branch --show-current)"
    echo "Last commit: $(git log -1 --oneline)"
    echo "Repository status:"
    git status --porcelain
    
    # Check if there are unpulled changes
    git fetch origin >/dev/null 2>&1
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "no-upstream")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_success "Repository is up to date"
    else
        log_error "Repository is NOT up to date - you need to pull changes!"
        echo "Run: git pull origin $(git branch --show-current)"
    fi
else
    log_error "Not a Git repository!"
fi
echo ""

# 2. Check template files
log_info "2. Checking template files..."
TEMPLATE_FILE="users/templates/users/patient_registration.html"
if [ -f "$TEMPLATE_FILE" ]; then
    log_success "Registration template found"
    
    # Check for specific fields
    if grep -q "blood_type" "$TEMPLATE_FILE"; then
        log_success "Blood type field found in template"
    else
        log_error "Blood type field MISSING from template"
    fi
    
    if grep -q "address" "$TEMPLATE_FILE"; then
        log_success "Address field found in template"
    else
        log_error "Address field MISSING from template"
    fi
    
    if grep -q "date_of_birth" "$TEMPLATE_FILE"; then
        log_success "Date of birth field found in template"
    else
        log_error "Date of birth field MISSING from template"
    fi
    
    if grep -q "gender" "$TEMPLATE_FILE"; then
        log_success "Gender field found in template"
    else
        log_error "Gender field MISSING from template"
    fi
else
    log_error "Registration template NOT found at $TEMPLATE_FILE"
fi
echo ""

# 3. Check form files
log_info "3. Checking form files..."
FORM_FILE="users/forms.py"
if [ -f "$FORM_FILE" ]; then
    log_success "Forms file found"
    
    if grep -q "blood_type" "$FORM_FILE"; then
        log_success "Blood type field found in forms"
    else
        log_error "Blood type field MISSING from forms"
    fi
    
    if grep -q "address" "$FORM_FILE"; then
        log_success "Address field found in forms"
    else
        log_error "Address field MISSING from forms"
    fi
else
    log_error "Forms file NOT found at $FORM_FILE"
fi
echo ""

# 4. Check static files
log_info "4. Checking static files..."
if [ -d "staticfiles" ] || [ -d "static" ]; then
    log_success "Static files directory found"
    
    # Check when static files were last collected
    if [ -d "staticfiles" ]; then
        STATIC_DATE=$(stat -c %y staticfiles 2>/dev/null || echo "Unknown")
        echo "Static files last updated: $STATIC_DATE"
    fi
else
    log_warning "Static files directory not found - run collectstatic"
fi
echo ""

# 5. Check running processes
log_info "5. Checking running Django processes..."
DJANGO_PROCESSES=$(ps aux | grep -E "(manage.py|gunicorn)" | grep -v grep || true)
if [ -n "$DJANGO_PROCESSES" ]; then
    log_warning "Django processes are running:"
    echo "$DJANGO_PROCESSES"
    echo ""
    log_warning "You may need to restart the server to see changes!"
else
    log_info "No Django processes currently running"
fi
echo ""

# 6. Check database migrations
log_info "6. Checking database migrations..."
if [ -f "manage.py" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        if [ -f ".env" ]; then
            export $(grep -v '^#' .env | xargs) 2>/dev/null || true
        fi
        
        echo "Migration status:"
        python manage.py showmigrations --plan 2>/dev/null | tail -10 || log_error "Could not check migrations"
    else
        log_error "Virtual environment not found"
    fi
else
    log_error "manage.py not found"
fi
echo ""

# 7. Check .env file
log_info "7. Checking environment configuration..."
if [ -f ".env" ]; then
    log_success ".env file found"
    echo "Database configuration:"
    grep -E "(DATABASE_URL|USE_SQLITE)" .env || log_warning "Database config not found in .env"
else
    log_error ".env file NOT found"
fi
echo ""

# 8. Summary and recommendations
echo "🔧 DIAGNOSTIC SUMMARY"
echo "===================="
echo ""

# Check if template has the fields
if [ -f "$TEMPLATE_FILE" ] && grep -q "blood_type" "$TEMPLATE_FILE" && grep -q "address" "$TEMPLATE_FILE"; then
    log_success "Your code HAS the latest signup form with all fields"
    echo ""
    echo "🚨 LIKELY ISSUES:"
    echo "1. Server needs restart - old code still running in memory"
    echo "2. Static files not updated - run collectstatic"
    echo "3. Browser cache - try hard refresh (Ctrl+F5)"
    echo ""
    echo "🔧 QUICK FIX:"
    echo "1. Stop your Django server"
    echo "2. Run: python manage.py collectstatic --noinput"
    echo "3. Restart your Django server"
    echo "4. Hard refresh your browser (Ctrl+F5)"
else
    log_error "Your code is MISSING the latest signup form"
    echo ""
    echo "🚨 YOU NEED TO UPDATE YOUR CODE:"
    echo "1. Run: git pull origin master"
    echo "2. Run: python manage.py migrate"
    echo "3. Run: python manage.py collectstatic --noinput"
    echo "4. Restart your server"
fi

echo ""
echo "For automatic fix, run: ./update-vps-system.sh"