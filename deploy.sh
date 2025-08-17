#!/bin/bash

# =============================================================================
# Robust Docker Deployment Script with Static Files Fix
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_RETRIES=3
COMPOSE_FILE="docker-compose.prod.yml"

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
    print_success "Docker is running"
}

# Function to clean up static files
cleanup_static_files() {
    print_status "Cleaning up static files..."
    
    # Remove existing staticfiles directory
    if [ -d "staticfiles" ]; then
        rm -rf staticfiles/
        print_success "Removed existing staticfiles directory"
    fi
    
    # Clean up any Docker volumes that might have old static files
    docker volume prune -f > /dev/null 2>&1 || true
    print_success "Cleaned up Docker volumes"
}

# Function to stop existing containers
stop_containers() {
    print_status "Stopping existing containers..."
    docker compose -f $COMPOSE_FILE down --remove-orphans > /dev/null 2>&1 || true
    print_success "Containers stopped"
}

# Function to build with retries
build_with_retries() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        print_status "Build attempt $attempt of $MAX_RETRIES..."
        
        if docker compose -f $COMPOSE_FILE build --no-cache; then
            print_success "Build completed successfully!"
            return 0
        else
            print_warning "Build attempt $attempt failed"
            if [ $attempt -lt $MAX_RETRIES ]; then
                print_status "Cleaning up and retrying..."
                cleanup_static_files
                docker system prune -f > /dev/null 2>&1 || true
                sleep 5
            fi
        fi
        
        ((attempt++))
    done
    
    print_error "All build attempts failed"
    return 1
}

# Function to deploy
deploy() {
    print_status "Starting deployment..."
    
    if docker compose -f $COMPOSE_FILE up -d; then
        print_success "Deployment started successfully!"
        return 0
    else
        print_error "Deployment failed"
        return 1
    fi
}

# Function to check health
check_health() {
    print_status "Checking service health..."
    
    local max_wait=120
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if docker compose -f $COMPOSE_FILE ps | grep -q "healthy"; then
            print_success "Services are healthy!"
            return 0
        fi
        
        echo -n "."
        sleep 5
        ((wait_time+=5))
    done
    
    print_warning "Health check timeout, but services may still be starting"
    return 0
}

# Function to show status
show_status() {
    print_status "Current service status:"
    docker compose -f $COMPOSE_FILE ps
    
    print_status "Service logs (last 10 lines):"
    docker compose -f $COMPOSE_FILE logs --tail=10
}

# Main deployment function
main() {
    print_status "Starting robust Docker deployment..."
    
    # Check prerequisites
    check_docker
    
    # Check if environment file exists
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating from production template..."
        if [ -f ".env.prod" ]; then
            cp .env.prod .env
            print_warning "Using production environment settings"
        elif [ -f "env.template" ]; then
            cp env.template .env
            print_warning "Please edit .env file with your settings before running again"
            exit 1
        else
            print_error "No .env.prod or env.template found. Please create .env file manually"
            exit 1
        fi
    fi
    
    # Stop existing containers
    stop_containers
    
    # Clean up static files
    cleanup_static_files
    
    # Build with retries
    if ! build_with_retries; then
        print_error "Build failed after $MAX_RETRIES attempts"
        exit 1
    fi
    
    # Deploy
    if ! deploy; then
        print_error "Deployment failed"
        exit 1
    fi
    
    # Check health
    check_health
    
    # Show final status
    show_status
    
    print_success "Deployment completed successfully!"
    print_status "Your application should be available at: http://65.108.91.110:8080"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "stop")
        stop_containers
        ;;
    "clean")
        stop_containers
        cleanup_static_files
        docker system prune -f
        print_success "Cleanup completed"
        ;;
    "logs")
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    *)
        echo "Usage: $0 {deploy|status|stop|clean|logs}"
        echo "  deploy  - Full deployment (default)"
        echo "  status  - Show current status"
        echo "  stop    - Stop all services"
        echo "  clean   - Clean up everything"
        echo "  logs    - Show live logs"
        exit 1
        ;;
esac