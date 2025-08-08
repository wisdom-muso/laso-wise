#!/bin/bash

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

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to stop existing containers
stop_containers() {
    print_status "Stopping any existing containers..."
    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        print_success "Existing containers stopped"
    else
        print_status "No running containers found"
    fi
}

# Function to run in development mode
run_development() {
    print_status "Starting application in development mode..."
    print_status "Access the application at http://localhost:8000"
    
    docker-compose up --build
}

# Function to run in production mode
run_production() {
    print_status "Starting application in production mode..."
    print_status "Access the application at http://localhost"
    
    # Stop any existing containers first
    stop_containers
    
    # Build and run production containers
    docker-compose -f docker-compose.prod.yml up --build -d
    
    # Show running containers
    print_status "Running containers:"
    docker-compose -f docker-compose.prod.yml ps
    
    print_success "Application started in production mode"
    print_status "Use 'docker-compose -f docker-compose.prod.yml logs -f' to view logs"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  dev, development    Run in development mode (default)"
    echo "  prod, production    Run in production mode"
    echo "  stop                Stop all running containers"
    echo "  clean               Stop containers and remove volumes"
    echo "  help, -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run in development mode"
    echo "  $0 dev              # Run in development mode"
    echo "  $0 production       # Run in production mode"
    echo "  $0 stop             # Stop all containers"
}

# Function to clean up
clean_up() {
    print_status "Stopping containers and removing volumes..."
    docker-compose down -v
    docker-compose -f docker-compose.prod.yml down -v
    print_success "Cleanup completed"
}

# Main script logic
case "${1:-dev}" in
    "dev"|"development")
        check_docker
        run_development
        ;;
    "prod"|"production")
        check_docker
        run_production
        ;;
    "stop")
        check_docker
        stop_containers
        docker-compose -f docker-compose.prod.yml down
        print_success "All containers stopped"
        ;;
    "clean")
        check_docker
        clean_up
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac