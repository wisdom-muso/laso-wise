#!/bin/bash

# LASO Healthcare - Deployment Diagnostic Script
# This script helps diagnose deployment issues

echo "🔍 LASO Healthcare - Deployment Diagnostics"
echo "==========================================="

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

# Check Docker status
print_status "Checking Docker status..."
if docker info >/dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
fi

# Check running containers
print_status "Checking running containers..."
echo "Current containers:"
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# Check for PostgreSQL container specifically
print_status "Checking for PostgreSQL container..."
if docker ps -a | grep -q "laso_postgres\|postgres"; then
    postgres_status=$(docker ps -a --filter "name=laso_postgres" --format "{{.Status}}")
    if echo "$postgres_status" | grep -q "Up"; then
        print_success "PostgreSQL container is running: $postgres_status"
    else
        print_error "PostgreSQL container exists but is not running: $postgres_status"
        print_status "PostgreSQL container logs:"
        docker logs laso_postgres 2>&1 | tail -20
    fi
else
    print_error "PostgreSQL container not found"
fi

# Check Docker Compose services
print_status "Checking Docker Compose services..."
if [ -f "docker-compose.yml" ]; then
    print_status "Docker Compose service status:"
    docker-compose ps
else
    print_error "docker-compose.yml not found"
fi

# Check environment file
print_status "Checking environment configuration..."
if [ -f ".env" ]; then
    print_success ".env file exists"
    print_status "Database configuration:"
    grep -E "^(POSTGRES_|DATABASE_|USE_SQLITE)" .env || echo "No database config found in .env"
else
    print_warning ".env file not found"
fi

# Check network connectivity
print_status "Checking Docker network..."
if docker network ls | grep -q "laso_network\|laso-wise"; then
    network_name=$(docker network ls | grep -E "laso_network|laso-wise" | awk '{print $2}' | head -1)
    print_success "Docker network found: $network_name"
    print_status "Network details:"
    docker network inspect "$network_name" --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
else
    print_warning "LASO Docker network not found"
fi

# Check volumes
print_status "Checking Docker volumes..."
print_status "LASO-related volumes:"
docker volume ls | grep -E "laso|postgres" || echo "No LASO-related volumes found"

# Check ports
print_status "Checking port usage..."
print_status "Ports 3000, 5432, 6379, 8081:"
netstat -tlnp 2>/dev/null | grep -E ":3000|:5432|:6379|:8081" || echo "No services found on expected ports"

# Test database connectivity if container is running
if docker ps | grep -q "laso_postgres"; then
    print_status "Testing database connectivity..."
    if docker exec laso_postgres pg_isready -U laso_user -d laso_healthcare >/dev/null 2>&1; then
        print_success "Database is accepting connections"
    else
        print_error "Database is not accepting connections"
    fi
fi

# Check web service logs if container exists
if docker ps -a | grep -q "laso_web"; then
    print_status "Recent web service logs:"
    docker logs laso_web 2>&1 | tail -10
fi

print_status "Diagnostic complete!"
echo ""
print_status "Common solutions:"
echo "1. If PostgreSQL container is missing: Run './fix-database-startup.sh'"
echo "2. If containers are stopped: Run 'docker-compose up -d'"
echo "3. If database connection fails: Check .env file and restart services"
echo "4. If ports are in use: Stop conflicting services or change ports"