#!/bin/bash

# LASO Healthcare System - PostgreSQL Setup for VPS
# This script sets up PostgreSQL database on Ubuntu VPS

set -e

echo "🐘 LASO Healthcare - PostgreSQL VPS Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Database configuration from .env file
DB_NAME="laso_healthcare"
DB_USER="laso_user"
DB_PASSWORD="laso2403"

log_info "Starting PostgreSQL setup for LASO Healthcare System..."

# Update system packages
log_info "Updating system packages..."
sudo apt update

# Install PostgreSQL
log_info "Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL service
log_info "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check PostgreSQL status
if sudo systemctl is-active --quiet postgresql; then
    log_success "PostgreSQL service is running"
else
    log_error "PostgreSQL service failed to start"
    exit 1
fi

# Create database and user
log_info "Setting up database and user..."

# Switch to postgres user and create database/user
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

-- Show created database and user
\l
\du
EOF

if [ $? -eq 0 ]; then
    log_success "Database and user created successfully"
else
    log_error "Failed to create database and user"
    exit 1
fi

# Update .env file to use localhost instead of 'db'
log_info "Updating .env file for VPS deployment..."

if [ -f ".env" ]; then
    # Backup original .env
    cp .env .env.backup
    log_info "Backed up original .env to .env.backup"
    
    # Update DATABASE_URL to use localhost
    sed -i 's|DATABASE_URL=postgresql://laso_user:laso2403@db:5432/laso_healthcare|DATABASE_URL=postgresql://laso_user:laso2403@localhost:5432/laso_healthcare|g' .env
    
    # Ensure USE_SQLITE is False
    sed -i 's/USE_SQLITE=.*/USE_SQLITE=False/' .env
    
    log_success "Updated .env file for VPS PostgreSQL configuration"
else
    log_error ".env file not found"
    exit 1
fi

# Test database connection
log_info "Testing database connection..."

# Install psycopg2 dependencies if not already installed
sudo apt install -y python3-dev libpq-dev

# Test connection using psql
if PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
    log_success "Database connection test passed"
else
    log_error "Database connection test failed"
    exit 1
fi

# Configure PostgreSQL for local connections
log_info "Configuring PostgreSQL authentication..."

# Find PostgreSQL version and config directory
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

if [ -d "$PG_CONFIG_DIR" ]; then
    # Backup original pg_hba.conf
    sudo cp "$PG_CONFIG_DIR/pg_hba.conf" "$PG_CONFIG_DIR/pg_hba.conf.backup"
    
    # Ensure local connections are allowed
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" "$PG_CONFIG_DIR/postgresql.conf"
    
    # Restart PostgreSQL to apply changes
    sudo systemctl restart postgresql
    
    log_success "PostgreSQL configuration updated"
else
    log_warning "Could not find PostgreSQL config directory, using default settings"
fi

# Final connection test
log_info "Performing final connection test..."
if PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 'PostgreSQL is ready for LASO Healthcare!' as status;" 2>/dev/null; then
    log_success "PostgreSQL setup completed successfully!"
else
    log_error "Final connection test failed"
    exit 1
fi

echo ""
echo "🎉 PostgreSQL Setup Complete!"
echo "=============================="
echo "✅ PostgreSQL installed and running"
echo "✅ Database: $DB_NAME"
echo "✅ User: $DB_USER"
echo "✅ Host: localhost:5432"
echo "✅ .env file updated for VPS"
echo ""
echo "Next steps:"
echo "1. Run: ./run-migrations.sh"
echo "2. Start your Django application"
echo ""
echo "Database connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""