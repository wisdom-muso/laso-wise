#!/bin/bash

# =============================================================================
# LASO Digital Health - Backup Script
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="laso_backup_${TIMESTAMP}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Load environment variables if available
if [[ -f "${PROJECT_ROOT}/.env.prod" ]]; then
    set -a
    source "${PROJECT_ROOT}/.env.prod"
    set +a
fi

# Default configuration
BACKUP_ENABLED=${BACKUP_ENABLED:-true}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-laso}

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

# Function to check if backup is enabled
check_backup_enabled() {
    if [[ "$BACKUP_ENABLED" != "true" ]]; then
        print_warning "Backup is disabled in configuration"
        exit 0
    fi
}

# Function to create backup directory
create_backup_dir() {
    local backup_path="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# Function to backup database
backup_database() {
    local backup_path="$1"
    
    print_status "Backing up database..."
    
    # Check if using SQLite
    if [[ -f "${PROJECT_ROOT}/db.sqlite3" ]]; then
        print_status "Backing up SQLite database..."
        cp "${PROJECT_ROOT}/db.sqlite3" "${backup_path}/db.sqlite3"
        print_success "SQLite database backed up"
        return 0
    fi
    
    # Check if using PostgreSQL in Docker
    if docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" ps db | grep -q "Up"; then
        print_status "Backing up PostgreSQL database..."
        
        # Get database credentials from environment
        DB_NAME=${POSTGRES_DB:-laso_db}
        DB_USER=${POSTGRES_USER:-laso_user}
        DB_PASSWORD=${POSTGRES_PASSWORD:-}
        
        # Create database dump
        docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db pg_dump \
            -U "$DB_USER" -d "$DB_NAME" --no-password > "${backup_path}/database.sql"
        
        # Also create a compressed version
        gzip -c "${backup_path}/database.sql" > "${backup_path}/database.sql.gz"
        
        print_success "PostgreSQL database backed up"
        return 0
    fi
    
    print_warning "No database found to backup"
}

# Function to backup media files
backup_media() {
    local backup_path="$1"
    
    print_status "Backing up media files..."
    
    # Check if media directory exists
    if [[ -d "${PROJECT_ROOT}/media" ]] && [[ "$(ls -A "${PROJECT_ROOT}/media" 2>/dev/null)" ]]; then
        tar -czf "${backup_path}/media.tar.gz" -C "${PROJECT_ROOT}" media/
        print_success "Media files backed up"
    else
        print_warning "No media files found to backup"
    fi
}

# Function to backup static files (optional)
backup_static() {
    local backup_path="$1"
    
    print_status "Backing up static files..."
    
    if [[ -d "${PROJECT_ROOT}/staticfiles" ]] && [[ "$(ls -A "${PROJECT_ROOT}/staticfiles" 2>/dev/null)" ]]; then
        tar -czf "${backup_path}/staticfiles.tar.gz" -C "${PROJECT_ROOT}" staticfiles/
        print_success "Static files backed up"
    else
        print_warning "No static files found to backup"
    fi
}

# Function to backup configuration files
backup_config() {
    local backup_path="$1"
    
    print_status "Backing up configuration files..."
    
    # Backup Docker configuration
    cp "${PROJECT_ROOT}/docker-compose.prod.yml" "${backup_path}/" 2>/dev/null || true
    cp "${PROJECT_ROOT}/Dockerfile.prod" "${backup_path}/" 2>/dev/null || true
    
    # Backup environment files (without sensitive data)
    if [[ -f "${PROJECT_ROOT}/.env.prod" ]]; then
        # Create sanitized version of environment file
        grep -v -E "(PASSWORD|SECRET|KEY)" "${PROJECT_ROOT}/.env.prod" > "${backup_path}/.env.prod.template" || true
    fi
    
    # Backup nginx configuration
    if [[ -d "${PROJECT_ROOT}/deployment/nginx" ]]; then
        cp -r "${PROJECT_ROOT}/deployment/nginx" "${backup_path}/"
    fi
    
    print_success "Configuration files backed up"
}

# Function to create backup manifest
create_manifest() {
    local backup_path="$1"
    
    print_status "Creating backup manifest..."
    
    cat > "${backup_path}/manifest.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)",
    "project_root": "${PROJECT_ROOT}",
    "files": [
$(find "$backup_path" -type f -printf '        "%f",\n' | sed '$ s/,$//')
    ],
    "size_bytes": $(du -sb "$backup_path" | cut -f1),
    "version": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
}
EOF
    
    print_success "Backup manifest created"
}

# Function to compress backup
compress_backup() {
    local backup_path="$1"
    
    print_status "Compressing backup..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    # Remove uncompressed backup
    rm -rf "$BACKUP_NAME"
    
    local compressed_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    print_success "Backup compressed to ${compressed_size}"
}

# Function to upload to S3 (if configured)
upload_to_s3() {
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    if [[ -n "${BACKUP_S3_BUCKET:-}" ]] && [[ -n "${BACKUP_S3_ACCESS_KEY:-}" ]] && [[ -n "${BACKUP_S3_SECRET_KEY:-}" ]]; then
        print_status "Uploading backup to S3..."
        
        # Check if AWS CLI is available
        if command -v aws &> /dev/null; then
            export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY"
            export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
            
            aws s3 cp "$backup_file" "s3://${BACKUP_S3_BUCKET}/laso-backups/" --no-progress
            print_success "Backup uploaded to S3"
        else
            print_warning "AWS CLI not available, skipping S3 upload"
        fi
    else
        print_status "S3 backup not configured, skipping upload"
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    print_status "Cleaning up old backups..."
    
    # Remove local backups older than retention period
    find "$BACKUP_DIR" -name "laso_backup_*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
    
    # Remove old log files
    find "$BACKUP_DIR" -name "backup.log.*" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
    
    print_success "Old backups cleaned up"
}

# Function to send notification (webhook or email)
send_notification() {
    local status="$1"
    local message="$2"
    
    # Example webhook notification (customize as needed)
    if [[ -n "${BACKUP_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$BACKUP_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"LASO Backup $status: $message\"}" \
            --max-time 10 --silent || true
    fi
}

# Main backup function
main() {
    print_status "Starting LASO Digital Health backup..."
    echo "===========================================" >> "$LOG_FILE"
    echo "Backup started at: $(date)" >> "$LOG_FILE"
    echo "===========================================" >> "$LOG_FILE"
    
    # Check if backup is enabled
    check_backup_enabled
    
    # Create backup directory
    local backup_path
    backup_path=$(create_backup_dir)
    
    # Perform backup operations
    backup_database "$backup_path"
    backup_media "$backup_path"
    backup_static "$backup_path"
    backup_config "$backup_path"
    create_manifest "$backup_path"
    
    # Compress backup
    compress_backup "$backup_path"
    
    # Upload to S3 if configured
    upload_to_s3
    
    # Clean old backups
    cleanup_old_backups
    
    # Calculate final backup size
    local final_size=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
    
    print_success "Backup completed successfully!"
    print_status "Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    print_status "Backup size: $final_size"
    
    # Send success notification
    send_notification "SUCCESS" "Backup completed successfully (${final_size})"
    
    echo "===========================================" >> "$LOG_FILE"
    echo "Backup completed at: $(date)" >> "$LOG_FILE"
    echo "===========================================" >> "$LOG_FILE"
}

# Function to show help
show_help() {
    cat << EOF
LASO Digital Health - Backup Script

Usage: $0 [OPTIONS]

Options:
  --help, -h           Show this help message
  --no-compress        Skip compression of backup
  --no-upload          Skip S3 upload
  --no-cleanup         Skip cleanup of old backups
  --dry-run            Show what would be backed up without doing it

Examples:
  $0                   # Full backup with all options
  $0 --no-upload       # Backup without S3 upload
  $0 --dry-run         # Show what would be backed up

Configuration:
  Set environment variables in .env.prod:
  - BACKUP_ENABLED=true
  - BACKUP_RETENTION_DAYS=30
  - BACKUP_S3_BUCKET=your-bucket
  - BACKUP_S3_ACCESS_KEY=your-key
  - BACKUP_S3_SECRET_KEY=your-secret
  - BACKUP_WEBHOOK_URL=https://hooks.slack.com/...

EOF
}

# Parse command line arguments
COMPRESS=true
UPLOAD=true
CLEANUP=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --no-upload)
            UPLOAD=false
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Handle dry run
if [[ "$DRY_RUN" == "true" ]]; then
    print_status "DRY RUN - Would backup:"
    [[ -f "${PROJECT_ROOT}/db.sqlite3" ]] && echo "  - SQLite database"
    docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" ps db | grep -q "Up" && echo "  - PostgreSQL database"
    [[ -d "${PROJECT_ROOT}/media" ]] && echo "  - Media files"
    [[ -d "${PROJECT_ROOT}/staticfiles" ]] && echo "  - Static files"
    echo "  - Configuration files"
    exit 0
fi

# Error handling
trap 'print_error "Backup failed with error"; send_notification "FAILED" "Backup failed with error"; exit 1' ERR

# Run main function
main "$@"
