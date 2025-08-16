#!/bin/bash

# =============================================================================
# Django + React Development Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_CMD="docker compose"

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
    check_docker
    
    $COMPOSE_CMD up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully!"
        echo ""
        print_status "Services are now running:"
        echo -e "  🐍 Django Backend:  ${GREEN}http://localhost:8005${NC}"
        echo -e "  ⚕️  Django Admin:    ${GREEN}http://localhost:8005/admin${NC}"
        echo -e "  🗄️  API Endpoints:   ${GREEN}http://localhost:8005/api${NC}"
        echo -e "  ⚛️  React Frontend:  ${GREEN}http://localhost:3000${NC}"
        echo ""
        print_status "View logs with: ${YELLOW}./run.sh logs${NC}"
    else
        print_error "Failed to start services!"
        exit 1
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    $COMPOSE_CMD down
    print_success "Services stopped!"
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    $COMPOSE_CMD restart
    print_success "Services restarted!"
}

# Function to show logs
show_logs() {
    service=${1:-""}
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        $COMPOSE_CMD logs -f "$service"
    else
        print_status "Showing logs for all services..."
        $COMPOSE_CMD logs -f
    fi
}

# Function to show status
show_status() {
    print_status "Service status:"
    $COMPOSE_CMD ps
}

# Function to run Django management commands
django_command() {
    command="$1"
    print_status "Running Django command: $command"
    $COMPOSE_CMD exec django python manage.py $command
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    $COMPOSE_CMD exec django python manage.py createsuperuser
}

# Function to run migrations
run_migrations() {
    print_status "Running Django migrations..."
    $COMPOSE_CMD exec django python manage.py migrate
}

# Function to shell into container
shell() {
    service=${1:-"django"}
    print_status "Opening shell in $service container..."
    if [ "$service" = "django" ]; then
        $COMPOSE_CMD exec django bash
    elif [ "$service" = "frontend" ]; then
        $COMPOSE_CMD exec frontend sh
    else
        print_error "Unknown service: $service. Use 'django' or 'frontend'"
        exit 1
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    $COMPOSE_CMD down --volumes --remove-orphans
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
        shell)
            shell "$2"
            ;;
        manage)
            if [ -z "$2" ]; then
                print_error "Please provide a Django management command"
                exit 1
            fi
            django_command "$2"
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