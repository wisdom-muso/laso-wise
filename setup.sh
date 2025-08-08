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

print_status "Setting up Laso Digital Health Platform..."

# Check if .env file exists
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    if [ -f env.template ]; then
        cp env.template .env
        print_success ".env file created from template"
    else
        print_error "env.template not found. Please create a .env file manually."
        exit 1
    fi
else
    print_warning ".env file already exists. Skipping creation."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    print_status "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    print_status "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

print_success "Docker and Docker Compose are available"

# Make scripts executable
chmod +x run.sh
chmod +x collect_static.sh
chmod +x stop_containers.sh

print_success "Setup completed successfully!"
echo ""
print_status "Next steps:"
echo "  1. Edit .env file if needed (optional)"
echo "  2. Run the application:"
echo "     - Development: ./run.sh (http://localhost:8005)"
echo "     - Production: ./run.sh production (http://localhost:12000)"
echo "  3. Access the application:"
echo "     - Development: http://localhost:8005"
echo "     - Production: http://localhost:12000"
echo ""
print_status "For help, run: ./run.sh help" 