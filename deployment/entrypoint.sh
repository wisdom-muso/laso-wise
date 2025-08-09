#!/bin/sh

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

# Wait for database to be ready (if using external database)
wait_for_db() {
    if [ -n "$DATABASE_URL" ]; then
        print_status "Waiting for database to be ready..."
        # Extract host and port from DATABASE_URL if needed
        # This is a basic implementation - you might need to adjust based on your DB setup
        sleep 5
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    python manage.py migrate --noinput
    if [ $? -eq 0 ]; then
        print_success "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Create superuser if it doesn't exist
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        print_status "Creating superuser if it doesn't exist..."
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF
    fi
}

# Load initial data if needed
load_fixtures() {
    if [ "$LOAD_FIXTURES" = "true" ] && [ -f "fixtures/initial_data.json" ]; then
        print_status "Loading initial data fixtures..."
        python manage.py loaddata fixtures/initial_data.json
        if [ $? -eq 0 ]; then
            print_success "Initial data loaded successfully"
        else
            print_warning "Failed to load initial data (this might be expected if data already exists)"
        fi
    fi
}

# Health check function
health_check() {
    print_status "Performing application health check..."
    python manage.py check --deploy
    if [ $? -eq 0 ]; then
        print_success "Application health check passed"
    else
        print_error "Application health check failed"
        exit 1
    fi
}

# Main startup sequence
main() {
    print_status "Starting LASO Digital Health application..."
    
    # Wait for external services
    wait_for_db
    
    # Run health check
    health_check
    
    # Run migrations
    run_migrations
    
    # Create superuser if configured
    create_superuser
    
    # Load fixtures if configured
    load_fixtures
    
    print_success "Application startup sequence completed"
    
    # Start the application server
    print_status "Starting Gunicorn server..."
    exec gunicorn laso.wsgi:application \
        --bind 0.0.0.0:8005 \
        --workers ${GUNICORN_WORKERS:-3} \
        --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
        --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-50} \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --keepalive ${GUNICORN_KEEPALIVE:-2} \
        --preload \
        --access-logfile ${GUNICORN_ACCESS_LOG:-/home/appuser/app/logs/access.log} \
        --error-logfile ${GUNICORN_ERROR_LOG:-/home/appuser/app/logs/error.log} \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --capture-output
}

# Handle signals gracefully
trap 'print_status "Received termination signal, shutting down gracefully..."; exit 0' TERM INT

# Run main function
main "$@"
