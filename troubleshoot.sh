#!/bin/bash

# Laso Healthcare Troubleshooting Script
# This script helps diagnose and fix common deployment issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE"

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    $DOCKER_COMPOSE ps
    echo ""
    
    # Check if all services are healthy
    unhealthy_services=$($DOCKER_COMPOSE ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != "") | .Name' 2>/dev/null || echo "")
    
    if [ -z "$unhealthy_services" ]; then
        print_success "All services are healthy!"
    else
        print_warning "Some services are not healthy:"
        echo "$unhealthy_services"
    fi
}

# Function to test database connection
test_database() {
    print_status "Testing database connection..."
    if $DOCKER_COMPOSE exec -T web python manage.py shell << 'EOF'
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
    then
        print_success "Database test completed"
    else
        print_error "Database test failed"
    fi
}

# Function to test application health
test_application() {
    print_status "Testing application health..."
    if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
        print_success "Application health check passed!"
        curl -s http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null || echo "Health endpoint responded successfully"
    else
        print_error "Application health check failed"
        print_status "Checking web service logs..."
        $DOCKER_COMPOSE logs --tail=20 web
    fi
}

# Function to restart problematic services
restart_services() {
    print_status "Restarting services..."
    
    # Check if celery-beat is having issues
    if $DOCKER_COMPOSE logs celery-beat --tail=10 | grep -q "OperationalError\|ProgrammingError"; then
        print_warning "Celery Beat has database issues, restarting..."
        $DOCKER_COMPOSE restart celery-beat
        sleep 5
    fi
    
    print_success "Service restart completed"
}

# Function to show logs for all services
show_logs() {
    print_status "Showing recent logs for all services..."
    echo ""
    
    services=("db" "redis" "web" "celery" "celery-beat" "nginx")
    
    for service in "${services[@]}"; do
        echo -e "${BLUE}=== $service logs ===${NC}"
        $DOCKER_COMPOSE logs --tail=10 $service 2>/dev/null || echo "Service $service not found or not running"
        echo ""
    done
}

# Function to fix common issues
fix_common_issues() {
    print_status "Attempting to fix common issues..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file missing, creating default one..."
        cp .env.example .env 2>/dev/null || echo "No .env.example found"
    fi
    
    # Run migrations if needed
    print_status "Running database migrations..."
    $DOCKER_COMPOSE exec -T web python manage.py migrate --check >/dev/null 2>&1 || {
        print_warning "Migrations needed, running them..."
        $DOCKER_COMPOSE exec -T web python manage.py migrate
    }
    
    # Collect static files
    print_status "Collecting static files..."
    $DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput >/dev/null 2>&1 || {
        print_warning "Static file collection failed"
    }
    
    print_success "Common fixes applied"
}

# Main menu
case "${1:-help}" in
    "health")
        check_service_health
        ;;
    "db")
        test_database
        ;;
    "app")
        test_application
        ;;
    "logs")
        show_logs
        ;;
    "restart")
        restart_services
        ;;
    "fix")
        fix_common_issues
        ;;
    "full")
        print_status "Running full diagnostic..."
        check_service_health
        test_database
        test_application
        ;;
    "help"|*)
        echo "Laso Healthcare Troubleshooting Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  health    - Check service health status"
        echo "  db        - Test database connection"
        echo "  app       - Test application health endpoint"
        echo "  logs      - Show recent logs for all services"
        echo "  restart   - Restart problematic services"
        echo "  fix       - Apply common fixes"
        echo "  full      - Run full diagnostic (health + db + app)"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 health"
        echo "  $0 full"
        echo "  $0 logs"
        ;;
esac