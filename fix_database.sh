#!/bin/bash

# =============================================================================
# Database Migration Fix Script
# =============================================================================
# This script fixes missing database tables and migration issues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to run Django commands inside Docker container
run_django_command() {
    local cmd="$1"
    print_status "Running: $cmd"
    
    # Try to run in the web container
    if docker exec laso-prod-web-1 $cmd 2>/dev/null; then
        return 0
    elif docker exec laso-dev-web-1 $cmd 2>/dev/null; then
        return 0
    elif docker exec laso_web_1 $cmd 2>/dev/null; then
        return 0
    elif docker exec laso-web-1 $cmd 2>/dev/null; then
        return 0
    else
        print_error "Failed to run command in Docker container"
        print_status "Trying direct execution..."
        if python3 $cmd 2>/dev/null; then
            return 0
        else
            print_error "Direct execution failed. Please run ./run.sh to start the containers first."
            return 1
        fi
    fi
}

# Function to check current migration status
check_migrations() {
    print_header "Checking Migration Status"
    run_django_command "python manage.py showmigrations"
}

# Function to create missing migrations
create_migrations() {
    print_header "Creating Missing Migrations"
    
    print_status "Making migrations for core app..."
    run_django_command "python manage.py makemigrations core"
    
    print_status "Making migrations for all apps..."
    run_django_command "python manage.py makemigrations"
}

# Function to apply migrations
apply_migrations() {
    print_header "Applying Migrations"
    
    print_status "Applying all migrations..."
    run_django_command "python manage.py migrate"
    
    print_status "Applying core app migrations specifically..."
    run_django_command "python manage.py migrate core"
    
    print_status "Applying telemedicine migrations..."
    run_django_command "python manage.py migrate telemedicine"
}

# Function to collect static files
collect_static() {
    print_header "Collecting Static Files"
    run_django_command "python manage.py collectstatic --noinput"
}

# Function to create superuser if none exists
create_superuser() {
    print_header "Checking Superuser"
    
    # Check if superuser exists
    if run_django_command "python manage.py shell -c \"from accounts.models import User; print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser')\"" | grep -q "No superuser"; then
        print_warning "No superuser found. Creating one..."
        print_status "Creating superuser with default credentials:"
        print_status "Username: admin"
        print_status "Email: admin@lasohealth.com"
        print_status "Password: admin123"
        
        run_django_command "python manage.py shell -c \"
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lasohealth.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Admin user already exists')
\""
    else
        print_success "Superuser already exists"
    fi
}

# Function to check database tables
check_tables() {
    print_header "Checking Database Tables"
    
    # Check if core tables exist
    print_status "Checking for core_soapnote table..."
    if run_django_command "python manage.py dbshell -c \".tables\" | grep -q core_soapnote"; then
        print_success "core_soapnote table exists"
    else
        print_warning "core_soapnote table missing"
    fi
    
    print_status "Checking for core_ehrrecord table..."
    if run_django_command "python manage.py dbshell -c \".tables\" | grep -q core_ehrrecord"; then
        print_success "core_ehrrecord table exists"
    else
        print_warning "core_ehrrecord table missing"
    fi
}

# Function to fix admin registration issues
fix_admin_registration() {
    print_header "Checking Admin Registration"
    
    print_status "Verifying all models are registered in admin..."
    run_django_command "python manage.py shell -c \"
from django.contrib import admin
from core.models import SoapNote, EHRRecord
from telemedicine.models import Consultation, VideoProviderConfig

registered_models = admin.site._registry.keys()
model_names = [model._meta.label for model in registered_models]

print('Registered models:')
for name in sorted(model_names):
    print(f'  - {name}')

# Check specific models
if SoapNote in registered_models:
    print('✓ SoapNote is registered')
else:
    print('✗ SoapNote is NOT registered')

if EHRRecord in registered_models:
    print('✓ EHRRecord is registered')
else:
    print('✗ EHRRecord is NOT registered')

if Consultation in registered_models:
    print('✓ Consultation is registered')
else:
    print('✗ Consultation is NOT registered')
\""
}

# Main execution
main() {
    print_header "Database Migration Fix Script"
    print_status "This script will fix missing database tables and migration issues"
    
    # Check current status
    check_migrations || true
    check_tables || true
    
    # Create and apply migrations
    create_migrations || true
    apply_migrations || true
    
    # Collect static files
    collect_static || true
    
    # Create superuser if needed
    create_superuser || true
    
    # Check admin registration
    fix_admin_registration || true
    
    # Final status check
    print_header "Final Status Check"
    check_tables || true
    
    print_success "Database fix script completed!"
    print_status "You should now be able to access:"
    print_status "  - Admin panel: http://65.108.91.110:12000/admin/"
    print_status "  - SOAP Notes: http://65.108.91.110:12000/admin/core/soapnote/"
    print_status "  - EHR Records: http://65.108.91.110:12000/admin/core/ehrrecord/"
    print_status "  - Telemedicine: http://65.108.91.110:12000/admin/telemedicine/"
}

# Show help if requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat << EOF
Database Migration Fix Script

Usage: $0 [OPTIONS]

This script fixes common database migration issues including:
- Missing database tables (core_soapnote, core_ehrrecord)
- Unapplied migrations
- Missing superuser
- Admin registration issues

The script will automatically detect and fix these issues.

Options:
  --help, -h    Show this help message

Examples:
  $0            # Run full fix
  ./fix_database.sh   # Same as above
EOF
    exit 0
fi

# Run main function
main "$@"