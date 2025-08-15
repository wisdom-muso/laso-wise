#!/bin/bash

# =============================================================================
# LASO Digital Health - Professional Deployment Script
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="laso-digital-health"
COMPOSE_PROJECT_NAME="laso"
LOG_FILE="${SCRIPT_DIR}/deployment.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1" | tee -a "$LOG_FILE"
}

print_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1" | tee -a "$LOG_FILE"
    fi
}

# Function to log script start
log_start() {
    echo "===========================================" >> "$LOG_FILE"
    echo "Deployment started at: $(date)" >> "$LOG_FILE"
    echo "Command: $0 $*" >> "$LOG_FILE"
    echo "===========================================" >> "$LOG_FILE"
}

# Function to check system requirements
check_system_requirements() {
    print_header "Checking system requirements..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root is not recommended for security reasons"
    fi
    
    # Check available disk space (minimum 5GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        print_warning "Low disk space detected. At least 5GB recommended."
    fi
    
    # Check available memory (minimum 2GB)
    available_memory=$(free -m | grep '^Mem:' | awk '{print $7}')
    if [[ $available_memory -lt 2048 ]]; then
        print_warning "Low memory detected. At least 2GB RAM recommended."
    fi
    
    print_success "System requirements check completed"
}

# Function to check if Docker is installed
check_docker() {
    print_header "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        print_status "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker version
    docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    print_status "Docker version: $docker_version"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
        compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        print_status "Docker Compose version: $compose_version"
    elif docker compose version &> /dev/null; then
        compose_cmd="docker compose"
        compose_version=$(docker compose version --short)
        print_status "Docker Compose (plugin) version: $compose_version"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to check environment file
check_environment() {
    local env_file="$1"
    
    if [[ ! -f "$env_file" ]]; then
        print_warning "Environment file $env_file not found"
        if [[ "$env_file" == ".env.prod" ]]; then
            print_status "Creating production environment file from template..."
            cp env.template "$env_file"
            print_warning "Please edit $env_file with your production values before deployment"
            return 1
        fi
    else
        print_success "Environment file $env_file found"
        
        # Check for required variables in production
        if [[ "$env_file" == ".env.prod" ]]; then
            local required_vars=("SECRET_KEY" "DOMAIN" "ALLOWED_HOSTS")
            for var in "${required_vars[@]}"; do
                if ! grep -q "^${var}=" "$env_file" || grep -q "^${var}=.*change.*this" "$env_file"; then
                    print_warning "Please set $var in $env_file"
                fi
            done
        fi
    fi
    
    return 0
}

# Function to generate SSL certificates using Let's Encrypt
setup_ssl() {
    local domain="$1"
    
    print_header "Setting up SSL certificates for $domain..."
    
    if [[ "$domain" == "localhost" ]] || [[ "$domain" == "127.0.0.1" ]]; then
        print_status "Using self-signed certificates for local development"
        return 0
    fi
    
    # Create SSL directory
    mkdir -p deployment/nginx/ssl
    
    # Check if certbot is available
    if command -v certbot &> /dev/null; then
        print_status "Requesting Let's Encrypt certificate for $domain..."
        
        # Request certificate
        certbot certonly --standalone --non-interactive --agree-tos \
            --email "admin@$domain" -d "$domain" -d "www.$domain" || {
            print_warning "Failed to obtain Let's Encrypt certificate"
            print_status "Falling back to self-signed certificate"
        }
        
        # Copy certificates if successful
        if [[ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]]; then
            cp "/etc/letsencrypt/live/$domain/fullchain.pem" deployment/nginx/ssl/cert.pem
            cp "/etc/letsencrypt/live/$domain/privkey.pem" deployment/nginx/ssl/key.pem
            print_success "Let's Encrypt certificates installed"
        fi
    else
        print_warning "Certbot not found. Install certbot for automatic SSL certificate generation"
        print_status "Using self-signed certificates"
    fi
}

# Function to backup existing deployment
backup_deployment() {
    print_header "Creating deployment backup..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database if exists
    if [[ -f "db.sqlite3" ]]; then
        cp db.sqlite3 "$backup_dir/"
        print_status "Database backed up"
    fi
    
    # Backup media files
    if [[ -d "media" ]]; then
        cp -r media "$backup_dir/"
        print_status "Media files backed up"
    fi
    
    # Backup configuration
    cp docker-compose.prod.yml "$backup_dir/" 2>/dev/null || true
    cp .env.prod "$backup_dir/" 2>/dev/null || true
    
    print_success "Backup created in $backup_dir"
}

# Function to stop existing containers
stop_containers() {
    print_header "Stopping existing containers..."
    
    # Stop development containers
    if $compose_cmd ps | grep -q "Up"; then
        print_status "Stopping development containers..."
        $compose_cmd down
    fi
    
    # Stop production containers
    if $compose_cmd -f docker-compose.prod.yml ps | grep -q "Up"; then
        print_status "Stopping production containers..."
        $compose_cmd -f docker-compose.prod.yml down
    fi
    
    print_success "All containers stopped"
}

# Function to run in development mode
run_development() {
    print_header "Starting LASO Digital Health in Development Mode"
    
    # Check environment
    check_environment ".env.dev"
    
    # Ensure setup scripts are executable
    chmod +x setup_app.sh collect_static.sh 2>/dev/null || true
    
    # Run setup script to ensure proper directory structure
    print_status "Setting up application directory structure..."
    ./setup_app.sh
    
    print_status "Building and starting development containers..."
    print_status "Backend will be available at: http://localhost:8005"
    print_status "Frontend will be available at: http://localhost:3000"
    
    export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}-dev"
    
    # Start containers in detached mode
    $compose_cmd up --build --remove-orphans -d
    
    # Show running containers
    print_status "Running containers:"
    $compose_cmd ps
    
    # Show access URLs
    print_success "Application started in development mode!"
    print_status "Access URLs:"
    echo -e "  ${GREEN}Backend:${NC} http://localhost:8005"
    echo -e "  ${GREEN}Frontend:${NC} http://localhost:3000"
    echo -e "  ${GREEN}Admin Panel:${NC} http://localhost:8005/admin"
}

# Function to run in production mode
run_production() {
    print_header "Starting LASO Digital Health in Production Mode"
    
    # Check environment
    if ! check_environment ".env.prod"; then
        print_error "Production environment not properly configured"
        exit 1
    fi
    
    # Source environment variables
    set -a
    source .env.prod
    set +a
    
    # Setup SSL if domain is configured
    if [[ -n "${DOMAIN:-}" ]] && [[ "$DOMAIN" != "localhost" ]]; then
        setup_ssl "$DOMAIN"
    fi
    
    # Create backup
    backup_deployment
    
    # Stop existing containers
    stop_containers
    
    # Ensure setup scripts are executable
    chmod +x setup_app.sh collect_static.sh 2>/dev/null || true
    
    # Run setup script to ensure proper directory structure
    print_status "Setting up application directory structure..."
    ./setup_app.sh
    
    print_status "Building and starting production containers..."
    
    export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}-prod"
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Build and start containers
    $compose_cmd -f docker-compose.prod.yml up --build --remove-orphans -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Show running containers
    print_status "Running containers:"
    $compose_cmd -f docker-compose.prod.yml ps
    
    # Show service URLs
    local http_port="${HTTP_PORT:-80}"
    local https_port="${HTTPS_PORT:-443}"
    local domain="${DOMAIN:-localhost}"
    
    print_success "Application started in production mode!"
    print_status "Access URLs:"
    
    if [[ "${SSL_ENABLED:-false}" == "true" ]]; then
        if [[ "$https_port" == "443" ]]; then
            echo -e "  ${GREEN}HTTPS:${NC} https://$domain"
        else
            echo -e "  ${GREEN}HTTPS:${NC} https://$domain:$https_port"
        fi
    fi
    
    if [[ "$http_port" == "80" ]]; then
        echo -e "  ${GREEN}HTTP:${NC} http://$domain"
    else
        echo -e "  ${GREEN}HTTP:${NC} http://$domain:$http_port"
    fi
    
    echo -e "  ${GREEN}Frontend:${NC} http://$domain:3000"
    echo -e "  ${GREEN}Backend API:${NC} http://$domain:8005"
    echo -e "  ${GREEN}Admin Panel:${NC} http://$domain:8005/admin"
    
    print_status "Useful commands:"
    echo -e "  View logs: ${CYAN}$compose_cmd -f docker-compose.prod.yml logs -f${NC}"
    echo -e "  Stop services: ${CYAN}$0 stop${NC}"
    echo -e "  View status: ${CYAN}$compose_cmd -f docker-compose.prod.yml ps${NC}"
}

# Function to show logs
show_logs() {
    local service="${1:-}"
    
    if [[ -f "docker-compose.prod.yml" ]] && $compose_cmd -f docker-compose.prod.yml ps | grep -q "Up"; then
        print_status "Showing production logs..."
        if [[ -n "$service" ]]; then
            $compose_cmd -f docker-compose.prod.yml logs -f "$service"
        else
            $compose_cmd -f docker-compose.prod.yml logs -f
        fi
    else
        print_status "Showing development logs..."
        if [[ -n "$service" ]]; then
            $compose_cmd logs -f "$service"
        else
            $compose_cmd logs -f
        fi
    fi
}

# Function to show status
show_status() {
    print_header "Service Status"
    
    print_status "Development containers:"
    $compose_cmd ps 2>/dev/null || echo "No development containers running"
    
    echo ""
    print_status "Production containers:"
    $compose_cmd -f docker-compose.prod.yml ps 2>/dev/null || echo "No production containers running"
    
    echo ""
    print_status "Docker system info:"
    echo "Images: $(docker images -q | wc -l)"
    echo "Containers: $(docker ps -a -q | wc -l)"
    echo "Volumes: $(docker volume ls -q | wc -l)"
    echo "Networks: $(docker network ls -q | wc -l)"
}

# Function to update application
update_application() {
    print_header "Updating LASO Digital Health Application"
    
    # Pull latest changes
    if command -v git &> /dev/null && [[ -d ".git" ]]; then
        print_status "Pulling latest changes from repository..."
        git pull
    fi
    
    # Determine which environment is running
    if $compose_cmd -f docker-compose.prod.yml ps | grep -q "Up"; then
        print_status "Updating production deployment..."
        run_production
    else
        print_status "Updating development deployment..."
        run_development
    fi
}

# Function to clean up
clean_up() {
    print_header "Cleaning up Docker resources"
    
    print_status "Stopping and removing containers..."
    $compose_cmd down -v --remove-orphans 2>/dev/null || true
    $compose_cmd -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
    
    # Remove unused images
    print_status "Removing unused Docker images..."
    docker image prune -f
    
    # Remove unused volumes
    print_status "Removing unused Docker volumes..."
    docker volume prune -f
    
    # Remove unused networks
    print_status "Removing unused Docker networks..."
    docker network prune -f
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    cat << EOF
LASO Digital Health - Professional Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  dev, development     Start in development mode (default)
  prod, production     Start in production mode
  stop                 Stop all running containers
  restart              Restart the application
  update               Update and restart the application
  logs [service]       Show logs (optionally for specific service)
  status               Show status of all services
  clean                Clean up Docker resources
  backup               Create backup of current deployment
  ssl [domain]         Setup SSL certificates for domain
  health               Check application health
  shell [service]      Open shell in running container
  help, -h, --help     Show this help message

Options:
  --debug              Enable debug output
  --no-backup          Skip backup creation in production
  --force              Force operation without prompts

Examples:
  $0                   # Start in development mode
  $0 prod              # Start in production mode
  $0 logs web          # Show logs for web service
  $0 shell web         # Open shell in web container
  $0 clean             # Clean up Docker resources

Environment Files:
  .env.dev             Development environment variables
  .env.prod            Production environment variables (create from env.template)

For more information, visit: https://github.com/your-repo/laso-digital-health
EOF
}

# Function to check application health
check_health() {
    print_header "Checking Application Health"
    
    local health_url="http://localhost/health/"
    
    if curl -f -s "$health_url" > /dev/null 2>&1; then
        print_success "Application is healthy"
        
        # Check individual services
        print_status "Service health check:"
        $compose_cmd -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    else
        print_error "Application health check failed"
        print_status "Checking container status..."
        $compose_cmd -f docker-compose.prod.yml ps
    fi
}

# Function to open shell in container
open_shell() {
    local service="${1:-web}"
    
    print_status "Opening shell in $service container..."
    
    if $compose_cmd -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        $compose_cmd -f docker-compose.prod.yml exec "$service" /bin/sh
    elif $compose_cmd ps | grep -q "$service.*Up"; then
        $compose_cmd exec "$service" /bin/sh
    else
        print_error "Service $service is not running"
        exit 1
    fi
}

# Function to handle script interruption
cleanup_on_exit() {
    print_status "Script interrupted. Cleaning up..."
    exit 1
}

# Set up trap for cleanup
trap cleanup_on_exit INT TERM

# Main script logic
main() {
    # Initialize logging
    log_start "$@"
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug)
                DEBUG=true
                shift
                ;;
            --no-backup)
                NO_BACKUP=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Check system requirements
    check_system_requirements
    
    # Check Docker installation
    check_docker
    
    # Execute command
    case "${1:-dev}" in
        "dev"|"development")
            run_development
            ;;
        "prod"|"production")
            run_production
            ;;
        "stop")
            stop_containers
            ;;
        "restart")
            stop_containers
            sleep 5
            if [[ -f ".env.prod" ]] && $compose_cmd -f docker-compose.prod.yml ps | grep -q "Exited"; then
                run_production
            else
                run_development
            fi
            ;;
        "update")
            update_application
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "status")
            show_status
            ;;
        "clean")
            clean_up
            ;;
        "backup")
            backup_deployment
            ;;
        "ssl")
            setup_ssl "${2:-localhost}"
            ;;
        "health")
            check_health
            ;;
        "shell")
            open_shell "${2:-web}"
            ;;
        "help"|"-h"|"--help")
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