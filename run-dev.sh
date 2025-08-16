#!/bin/bash

# Development environment startup script for Django + React
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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build and start services
start_services() {
    print_status "Building and starting Django + React services..."
    
    # Build and start services
    docker-compose -f docker-compose.dev.yml up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully!"
        echo ""
        print_status "Services are now running:"
        echo -e "  🐍 Django Backend:  ${GREEN}http://localhost:8005${NC}"
        echo -e "  ⚕️  Django Admin:    ${GREEN}http://localhost:8005/admin${NC}"
        echo -e "  🗄️  API Endpoints:   ${GREEN}http://localhost:8005/api${NC}"
        echo -e "  ⚛️  React Frontend:  ${GREEN}http://localhost:3000${NC}"
        echo ""
        print_status "Health checks:"
        echo -e "  📊 Django Health:   ${GREEN}http://localhost:8005/api/health/${NC}"
        echo -e "  📊 React Health:    ${GREEN}http://localhost:3000/health${NC}"
        echo ""
        print_status "Logs can be viewed with:"
        echo -e "  ${YELLOW}docker-compose -f docker-compose.dev.yml logs -f${NC}"
    else
        print_error "Failed to start services!"
        exit 1
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose -f docker-compose.dev.yml down
    print_success "Services stopped!"
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    docker-compose -f docker-compose.dev.yml restart
    print_success "Services restarted!"
}

# Function to show logs
show_logs() {
    service=${1:-""}
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        docker-compose -f docker-compose.dev.yml logs -f "$service"
    else
        print_status "Showing logs for all services..."
        docker-compose -f docker-compose.dev.yml logs -f
    fi
}

# Function to show status
show_status() {
    print_status "Service status:"
    docker-compose -f docker-compose.dev.yml ps
}

# Function to run Django management commands
run_django_command() {
    command="$1"
    print_status "Running Django command: $command"
    docker-compose -f docker-compose.dev.yml exec django python manage.py $command
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    docker-compose -f docker-compose.dev.yml exec django python manage.py createsuperuser
}

# Function to run migrations
run_migrations() {
    print_status "Running Django migrations..."
    docker-compose -f docker-compose.dev.yml exec django python manage.py migrate
}

# Function to collect static files
collect_static() {
    print_status "Collecting static files..."
    docker-compose -f docker-compose.dev.yml exec django python manage.py collectstatic --noinput
}

# Function to shell into container
shell_into() {
    service=${1:-"django"}
    print_status "Opening shell in $service container..."
    if [ "$service" = "django" ]; then
        docker-compose -f docker-compose.dev.yml exec django bash
    elif [ "$service" = "frontend" ]; then
        docker-compose -f docker-compose.dev.yml exec frontend sh
    else
        print_error "Unknown service: $service. Use 'django' or 'frontend'"
        exit 1
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans
    docker system prune -f
    print_success "Cleanup completed!"
}

# Function to show help
show_help() {
    echo "Django + React Development Environment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start           Build and start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show service status"
    echo "  logs [service]  Show logs (optionally for specific service)"
    echo "  migrate         Run Django migrations"
    echo "  superuser       Create Django superuser"
    echo "  collectstatic   Collect Django static files"
    echo "  shell [service] Open shell in container (django/frontend)"
    echo "  manage <cmd>    Run Django management command"
    echo "  cleanup         Clean up Docker resources"
    echo "  help            Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs django"
    echo "  $0 shell frontend"
    echo "  $0 manage \"makemigrations\""
}

# Main script logic
main() {
    case "${1:-start}" in
        start)
            check_docker
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        migrate)
            run_migrations
            ;;
        superuser)
            create_superuser
            ;;
        collectstatic)
            collect_static
            ;;
        shell)
            shell_into "$2"
            ;;
        manage)
            if [ -z "$2" ]; then
                print_error "Please provide a Django management command"
                exit 1
            fi
            run_django_command "$2"
            ;;
        cleanup)
            cleanup
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"