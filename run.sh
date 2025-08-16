#!/bin/bash

# =============================================================================
# Django + React Production Deployment Script
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
VPS_IP="65.108.91.110"

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

# Function to create environment file if it doesn't exist
setup_env() {
    local env_file="$1"
    if [[ ! -f "$env_file" ]]; then
        print_status "Creating $env_file from template..."
        if [[ -f "env.template" ]]; then
            cp env.template "$env_file"
            print_warning "Please edit $env_file with your settings before running production"
        else
            # Create basic env file
            cat > "$env_file" << EOF
# Production Environment Variables
SECRET_KEY=your-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=$VPS_IP,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://$VPS_IP,https://$VPS_IP

# Database
POSTGRES_DB=laso_db
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=change-this-password

# Optional
CURRENCY=USD
HTTP_PORT=80
EOF
            print_warning "Created basic $env_file - please review and update the values"
        fi
    fi
}

# Function to build and start development services
start_dev() {
    print_status "Starting Django + React in DEVELOPMENT mode..."
    check_docker
    
    $COMPOSE_CMD up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "Development services started successfully!"
        echo ""
        print_status "Services are now running:"
        echo -e "  🐍 Django Backend:  ${GREEN}http://localhost:8005${NC}"
        echo -e "  ⚕️  Django Admin:    ${GREEN}http://localhost:8005/admin${NC}"
        echo -e "  🗄️  API Endpoints:   ${GREEN}http://localhost:8005/api${NC}"
        echo -e "  ⚛️  React Frontend:  ${GREEN}http://localhost:3000${NC}"
        echo ""
        print_status "View logs with: ${YELLOW}./run.sh logs${NC}"
    else
        print_error "Failed to start development services!"
        exit 1
    fi
}

# Function to build and start production services
start_prod() {
    print_status "Starting Django + React in PRODUCTION mode for VPS $VPS_IP..."
    check_docker
    
    # Setup environment
    setup_env ".env"
    
    # Source environment variables
    if [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    print_status "Building and starting production services..."
    $COMPOSE_CMD -f docker-compose.prod.yml up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "Production services started successfully!"
        echo ""
        print_status "🌐 Your application is now live at:"
        echo -e "  ${GREEN}http://$VPS_IP${NC} - Main Application"
        echo -e "  ${GREEN}http://$VPS_IP/admin${NC} - Django Admin"
        echo -e "  ${GREEN}http://$VPS_IP/api${NC} - API Endpoints"
        echo ""
        print_status "Services running:"
        echo -e "  📊 PostgreSQL Database"
        echo -e "  🐍 Django Backend (via nginx)"
        echo -e "  ⚛️  React Frontend (via nginx)"
        echo -e "  🌐 Nginx Reverse Proxy"
        echo ""
        print_status "Useful commands:"
        echo -e "  View logs: ${YELLOW}./run.sh logs${NC}"
        echo -e "  Check status: ${YELLOW}./run.sh status${NC}"
        echo -e "  Stop services: ${YELLOW}./run.sh stop${NC}"
    else
        print_error "Failed to start production services!"
        exit 1
    fi
}

# Function to stop services
stop_services() {
    local mode="${1:-both}"
    
    case "$mode" in
        "dev"|"development")
            print_status "Stopping development services..."
            $COMPOSE_CMD down
            ;;
        "prod"|"production")
            print_status "Stopping production services..."
            $COMPOSE_CMD -f docker-compose.prod.yml down
            ;;
        *)
            print_status "Stopping all services..."
            $COMPOSE_CMD down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.prod.yml down 2>/dev/null || true
            ;;
    esac
    print_success "Services stopped!"
}

# Function to restart services
restart_services() {
    local mode="${1:-auto}"
    
    if [[ "$mode" == "auto" ]]; then
        # Detect which services are running
        if $COMPOSE_CMD -f docker-compose.prod.yml ps | grep -q "Up"; then
            mode="prod"
        else
            mode="dev"
        fi
    fi
    
    print_status "Restarting services in $mode mode..."
    stop_services "$mode"
    sleep 2
    
    if [[ "$mode" == "prod" ]]; then
        start_prod
    else
        start_dev
    fi
}

# Function to show logs
show_logs() {
    local service="${1:-}"
    local mode="dev"
    
    # Detect which services are running
    if $COMPOSE_CMD -f docker-compose.prod.yml ps | grep -q "Up"; then
        mode="prod"
    fi
    
    if [[ "$mode" == "prod" ]]; then
        if [ -n "$service" ]; then
            print_status "Showing production logs for $service..."
            $COMPOSE_CMD -f docker-compose.prod.yml logs -f "$service"
        else
            print_status "Showing all production logs..."
            $COMPOSE_CMD -f docker-compose.prod.yml logs -f
        fi
    else
        if [ -n "$service" ]; then
            print_status "Showing development logs for $service..."
            $COMPOSE_CMD logs -f "$service"
        else
            print_status "Showing all development logs..."
            $COMPOSE_CMD logs -f
        fi
    fi
}

# Function to show status
show_status() {
    print_status "=== SERVICE STATUS ==="
    
    echo ""
    print_status "Development services:"
    $COMPOSE_CMD ps 2>/dev/null || echo "No development services running"
    
    echo ""
    print_status "Production services:"
    $COMPOSE_CMD -f docker-compose.prod.yml ps 2>/dev/null || echo "No production services running"
    
    echo ""
    print_status "Docker system info:"
    echo "Images: $(docker images -q | wc -l)"
    echo "Containers: $(docker ps -a -q | wc -l)"
    echo "Volumes: $(docker volume ls -q | wc -l)"
}

# Function to run Django management commands
django_command() {
    local command="$1"
    local mode="dev"
    
    # Detect which services are running
    if $COMPOSE_CMD -f docker-compose.prod.yml ps | grep -q "web.*Up"; then
        mode="prod"
        print_status "Running Django command in production: $command"
        $COMPOSE_CMD -f docker-compose.prod.yml exec web python manage.py $command
    elif $COMPOSE_CMD ps | grep -q "django.*Up"; then
        print_status "Running Django command in development: $command"
        $COMPOSE_CMD exec django python manage.py $command
    else
        print_error "No Django services are running. Start services first."
        exit 1
    fi
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    django_command "createsuperuser"
}

# Function to run migrations
run_migrations() {
    print_status "Running Django migrations..."
    django_command "migrate"
}

# Function to shell into container
shell() {
    local service="${1:-django}"
    local mode="dev"
    
    # Detect which services are running
    if $COMPOSE_CMD -f docker-compose.prod.yml ps | grep -q "Up"; then
        mode="prod"
    fi
    
    print_status "Opening shell in $service container ($mode mode)..."
    
    if [[ "$mode" == "prod" ]]; then
        case "$service" in
            "django"|"web")
                $COMPOSE_CMD -f docker-compose.prod.yml exec web bash
                ;;
            "frontend")
                $COMPOSE_CMD -f docker-compose.prod.yml exec frontend sh
                ;;
            "db"|"database")
                $COMPOSE_CMD -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER:-laso_user} -d ${POSTGRES_DB:-laso_db}
                ;;
            *)
                $COMPOSE_CMD -f docker-compose.prod.yml exec "$service" sh
                ;;
        esac
    else
        case "$service" in
            "django")
                $COMPOSE_CMD exec django bash
                ;;
            "frontend")
                $COMPOSE_CMD exec frontend sh
                ;;
            *)
                print_error "Unknown service: $service. Use 'django' or 'frontend'"
                exit 1
                ;;
        esac
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    $COMPOSE_CMD down --volumes --remove-orphans 2>/dev/null || true
    $COMPOSE_CMD -f docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f
    print_success "Cleanup completed!"
}

# Function to backup production database
backup_db() {
    if ! $COMPOSE_CMD -f docker-compose.prod.yml ps | grep -q "db.*Up"; then
        print_error "Production database is not running"
        exit 1
    fi
    
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_status "Creating database backup: $backup_file"
    
    $COMPOSE_CMD -f docker-compose.prod.yml exec -T db pg_dump -U ${POSTGRES_USER:-laso_user} -d ${POSTGRES_DB:-laso_db} > "$backup_file"
    print_success "Database backup created: $backup_file"
}

# Function to show help
show_help() {
    echo "Django + React VPS Deployment Script"
    echo "Configured for VPS: $VPS_IP"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [dev|prod]    Start services (default: dev)"
    echo "  stop [dev|prod]     Stop services"
    echo "  restart [dev|prod]  Restart services"
    echo "  status              Show service status"
    echo "  logs [service]      Show logs"
    echo "  migrate             Run Django migrations"
    echo "  superuser           Create Django superuser"
    echo "  shell [service]     Open shell (django/frontend/db)"
    echo "  manage <cmd>        Run Django management command"
    echo "  backup              Backup production database"
    echo "  cleanup             Clean up Docker resources"
    echo "  help                Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start prod       # Start production services"
    echo "  $0 logs nginx       # Show nginx logs"
    echo "  $0 shell db         # Open database shell"
    echo "  $0 backup           # Backup database"
    echo ""
    echo "Production URL: http://$VPS_IP"
}

# Main script logic
main() {
    case "${1:-start}" in
        start)
            case "${2:-dev}" in
                "prod"|"production")
                    start_prod
                    ;;
                *)
                    start_dev
                    ;;
            esac
            ;;
        stop)
            stop_services "$2"
            ;;
        restart)
            restart_services "$2"
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
        backup)
            backup_db
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