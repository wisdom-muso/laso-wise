#!/bin/bash

# =============================================================================
# Frontend Debug and Fix Script
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}"; }

# Function to check container logs
check_frontend_logs() {
    print_header "Checking Frontend Container Logs"
    
    local containers=("laso-dev-frontend-1" "laso_frontend_1" "laso-frontend-1")
    local found_container=""
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            found_container="$container"
            break
        fi
    done
    
    if [[ -n "$found_container" ]]; then
        print_status "Found frontend container: $found_container"
        print_status "Last 50 lines of logs:"
        echo "----------------------------------------"
        docker logs --tail 50 "$found_container" 2>&1 || true
        echo "----------------------------------------"
    else
        print_error "No frontend container found"
        print_status "Available containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}" || true
    fi
}

# Function to check if frontend is accessible
check_frontend_accessibility() {
    print_header "Checking Frontend Accessibility"
    
    local frontend_url="http://65.108.91.110:3000"
    
    print_status "Testing frontend URL: $frontend_url"
    
    if curl -s -f "$frontend_url" > /dev/null; then
        print_success "Frontend is responding"
        
        # Check if it's actually serving content
        local response=$(curl -s "$frontend_url" | head -10)
        if [[ "$response" == *"<div id=\"root\">"* ]]; then
            print_success "Frontend is serving HTML with root div"
        else
            print_warning "Frontend responding but may not be serving React app correctly"
            echo "Response preview:"
            echo "$response"
        fi
    else
        print_error "Frontend is not accessible at $frontend_url"
        
        # Try to get more info
        print_status "Trying to get error details..."
        curl -v "$frontend_url" 2>&1 | head -20 || true
    fi
}

# Function to verify environment variables
check_environment_variables() {
    print_header "Checking Environment Variables"
    
    local containers=("laso-dev-frontend-1" "laso_frontend_1" "laso-frontend-1")
    local found_container=""
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            found_container="$container"
            break
        fi
    done
    
    if [[ -n "$found_container" ]]; then
        print_status "Environment variables in container $found_container:"
        echo "----------------------------------------"
        docker exec "$found_container" env | grep -E "(VITE_|NODE_|API)" || echo "No VITE/NODE/API variables found"
        echo "----------------------------------------"
    else
        print_error "No frontend container found to check environment variables"
    fi
}

# Function to check file structure
check_file_structure() {
    print_header "Checking Frontend File Structure"
    
    print_status "Checking critical files exist..."
    
    local files=(
        "frontend/package.json"
        "frontend/index.html"
        "frontend/src/main.tsx"
        "frontend/src/lib/api.ts"
        "frontend/vite.config.ts"
        "frontend/.env"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "✓ $file exists"
        else
            print_error "✗ $file missing"
        fi
    done
}

# Function to rebuild frontend
rebuild_frontend() {
    print_header "Rebuilding Frontend"
    
    print_status "Stopping existing frontend container..."
    docker stop laso-dev-frontend-1 2>/dev/null || true
    
    print_status "Removing existing frontend container..."
    docker rm laso-dev-frontend-1 2>/dev/null || true
    
    print_status "Rebuilding and starting frontend..."
    docker-compose up --build frontend -d
    
    print_status "Waiting 10 seconds for container to start..."
    sleep 10
    
    print_status "Checking new container status..."
    docker ps | grep frontend || true
}

# Function to run diagnostics inside container
run_container_diagnostics() {
    print_header "Running Container Diagnostics"
    
    local containers=("laso-dev-frontend-1" "laso_frontend_1" "laso-frontend-1")
    local found_container=""
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            found_container="$container"
            break
        fi
    done
    
    if [[ -n "$found_container" ]]; then
        print_status "Running diagnostics in container: $found_container"
        
        echo "----------------------------------------"
        print_status "Working directory:"
        docker exec "$found_container" pwd
        
        print_status "Directory contents:"
        docker exec "$found_container" ls -la
        
        print_status "Node/NPM versions:"
        docker exec "$found_container" node --version
        docker exec "$found_container" npm --version
        
        print_status "Package.json exists?"
        docker exec "$found_container" ls -la package.json 2>/dev/null || echo "package.json not found in current directory"
        
        print_status "Frontend directory check:"
        docker exec "$found_container" ls -la /usr/src/app/frontend/ 2>/dev/null || echo "Frontend directory not found"
        
        print_status "Processes running:"
        docker exec "$found_container" ps aux
        
        print_status "Port 3000 status:"
        docker exec "$found_container" netstat -tlnp | grep 3000 || echo "Port 3000 not bound"
        
        echo "----------------------------------------"
    else
        print_error "No frontend container found for diagnostics"
    fi
}

# Function to fix common issues
fix_common_issues() {
    print_header "Fixing Common Issues"
    
    print_status "1. Ensuring .env.dev file exists..."
    if [[ ! -f ".env.dev" ]]; then
        print_status "Creating .env.dev file..."
        cat > .env.dev << EOF
# Development Environment
DEBUG=True
VITE_API_BASE=http://65.108.91.110:12000
FRONTEND_API_BASE=http://65.108.91.110:12000
NODE_ENV=development
EOF
        print_success "Created .env.dev file"
    else
        print_success ".env.dev file already exists"
    fi
    
    print_status "2. Ensuring frontend/.env file exists..."
    if [[ ! -f "frontend/.env" ]]; then
        print_status "Creating frontend/.env file..."
        cat > frontend/.env << EOF
VITE_API_BASE=http://65.108.91.110:12000
VITE_APP_NAME=LASO Health
VITE_DEV_MODE=true
EOF
        print_success "Created frontend/.env file"
    else
        print_success "frontend/.env file already exists"
    fi
    
    print_status "3. Checking lib/api.ts file..."
    if [[ ! -f "frontend/src/lib/api.ts" ]]; then
        print_error "frontend/src/lib/api.ts is missing - this is critical!"
        print_status "This file should have been created in previous fixes"
    else
        print_success "frontend/src/lib/api.ts exists"
    fi
    
    print_status "4. Verifying docker-compose.yml configuration..."
    if grep -q "VITE_API_BASE.*8005" docker-compose.yml; then
        print_warning "Found old port 8005 in docker-compose.yml"
        print_status "This should be updated to port 12000"
    else
        print_success "docker-compose.yml looks correct"
    fi
}

# Function to show solution summary
show_solution_summary() {
    print_header "Solution Summary"
    
    cat << EOF
🎯 Common Causes of White Screen:

1. Missing API Configuration File
   - frontend/src/lib/api.ts must exist
   - Contains axios setup and endpoints

2. Environment Variables Not Set
   - VITE_API_BASE should be http://65.108.91.110:12000
   - Check .env files

3. Build/Start Process Issues
   - npm install failed
   - Build errors not visible
   - Port conflicts

4. Container Issues
   - Working directory wrong
   - Node modules not installed
   - Vite not starting properly

📋 Troubleshooting Steps:

1. Check container logs: ./debug_frontend.sh logs
2. Verify environment: ./debug_frontend.sh env
3. Rebuild frontend: ./debug_frontend.sh rebuild
4. Check file structure: ./debug_frontend.sh files

🔧 Quick Fixes:

# Stop and restart containers
docker-compose down
docker-compose up --build -d

# Check frontend specifically
docker logs laso-dev-frontend-1

# Access container shell
docker exec -it laso-dev-frontend-1 sh

# Test frontend URL
curl http://65.108.91.110:3000

🌐 Access URLs:
- Backend: http://65.108.91.110:12000
- Frontend: http://65.108.91.110:3000
- Admin: http://65.108.91.110:12000/admin/

EOF
}

# Main function
main() {
    case "${1:-all}" in
        "logs")
            check_frontend_logs
            ;;
        "access")
            check_frontend_accessibility
            ;;
        "env")
            check_environment_variables
            ;;
        "files")
            check_file_structure
            ;;
        "rebuild")
            rebuild_frontend
            ;;
        "diag")
            run_container_diagnostics
            ;;
        "fix")
            fix_common_issues
            ;;
        "help")
            show_solution_summary
            ;;
        "all"|*)
            print_header "Frontend Debugging - Full Diagnostic"
            check_file_structure
            fix_common_issues
            check_frontend_logs
            check_environment_variables
            run_container_diagnostics
            check_frontend_accessibility
            show_solution_summary
            ;;
    esac
}

# Help message
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat << EOF
Frontend Debug Script

Usage: $0 [COMMAND]

Commands:
  all      Run full diagnostic (default)
  logs     Check container logs
  access   Test frontend accessibility  
  env      Check environment variables
  files    Check file structure
  rebuild  Rebuild frontend container
  diag     Run container diagnostics
  fix      Fix common issues
  help     Show troubleshooting guide

Examples:
  $0              # Full diagnostic
  $0 logs         # Just check logs
  $0 rebuild      # Rebuild container
EOF
    exit 0
fi

main "$@"