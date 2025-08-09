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

# Set default values
DOMAIN=${DOMAIN:-localhost}
SSL_ENABLED=${SSL_ENABLED:-false}

print_status "Starting Nginx configuration setup..."
print_status "Domain: $DOMAIN"
print_status "SSL Enabled: $SSL_ENABLED"

# Function to generate self-signed certificate for development
generate_self_signed_cert() {
    print_status "Generating self-signed SSL certificate for development..."
    
    mkdir -p /etc/nginx/ssl
    
    # Generate DH parameters
    if [ ! -f /etc/nginx/ssl/dhparam.pem ]; then
        print_status "Generating DH parameters (this may take a while)..."
        openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
    fi
    
    # Generate self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/key.pem \
        -out /etc/nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    
    print_success "Self-signed certificate generated"
}

# Function to check for existing SSL certificates
check_ssl_certificates() {
    if [ "$SSL_ENABLED" = "true" ]; then
        if [ ! -f /etc/nginx/ssl/cert.pem ] || [ ! -f /etc/nginx/ssl/key.pem ]; then
            print_warning "SSL certificates not found, generating self-signed certificates"
            generate_self_signed_cert
        else
            print_success "SSL certificates found"
        fi
        
        # Check certificate validity
        if ! openssl x509 -in /etc/nginx/ssl/cert.pem -noout -checkend 86400; then
            print_warning "SSL certificate expires within 24 hours"
        fi
    fi
}

# Function to substitute environment variables in nginx config
substitute_env_vars() {
    print_status "Substituting environment variables in nginx configuration..."
    
    # Create a temporary file with environment variable substitutions
    envsubst '$DOMAIN $SSL_ENABLED' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
    mv /tmp/default.conf /etc/nginx/conf.d/default.conf
    
    print_success "Environment variables substituted"
}

# Function to validate nginx configuration
validate_config() {
    print_status "Validating nginx configuration..."
    
    if nginx -t; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration is invalid"
        exit 1
    fi
}

# Function to create log directories
setup_logging() {
    print_status "Setting up logging directories..."
    
    mkdir -p /var/log/nginx
    chown -R nginx:nginx /var/log/nginx
    
    # Create log files if they don't exist
    touch /var/log/nginx/access.log
    touch /var/log/nginx/error.log
    chown nginx:nginx /var/log/nginx/access.log
    chown nginx:nginx /var/log/nginx/error.log
    
    print_success "Logging setup completed"
}

# Function to wait for upstream services
wait_for_upstream() {
    print_status "Waiting for upstream Django service..."
    
    # Wait for Django service to be available
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f -s http://web:8005/health/ > /dev/null 2>&1; then
            print_success "Django service is ready"
            break
        fi
        
        print_status "Waiting for Django service... ($timeout seconds remaining)"
        sleep 5
        timeout=$((timeout-5))
    done
    
    if [ $timeout -le 0 ]; then
        print_warning "Django service not ready, continuing anyway..."
    fi
}

# Main setup function
main() {
    print_status "Initializing Nginx for LASO Digital Health..."
    
    # Setup logging
    setup_logging
    
    # Check SSL certificates
    check_ssl_certificates
    
    # Substitute environment variables
    substitute_env_vars
    
    # Validate configuration
    validate_config
    
    # Wait for upstream services (optional, comment out if not needed)
    # wait_for_upstream
    
    print_success "Nginx setup completed successfully"
    print_status "Starting Nginx..."
    
    # Start nginx
    exec "$@"
}

# Handle signals gracefully
trap 'print_status "Received termination signal, shutting down gracefully..."; exit 0' TERM INT

# Run main function
main "$@"
