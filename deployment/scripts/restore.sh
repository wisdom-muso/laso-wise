#!/bin/bash

# =============================================================================
# LASO Digital Health - Restore Script
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
RESTORE_DIR="${PROJECT_ROOT}/restore_temp"

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

# Function to list available backups
list_backups() {
    print_status "Available backups:"
    echo ""
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_warning "No backup directory found"
        return 1
    fi
    
    local backups=($(ls -1t "$BACKUP_DIR"/laso_backup_*.tar.gz 2>/dev/null || true))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        print_warning "No backups found"
        return 1
    fi
    
    for i in "${!backups[@]}"; do
        local backup_file="${backups[$i]}"
        local backup_name=$(basename "$backup_file" .tar.gz)
        local backup_date=$(echo "$backup_name" | sed 's/laso_backup_//' | sed 's/_/ /' | sed 's/\(.*\)_\(.*\)/\1 \2/')
        local backup_size=$(du -h "$backup_file" | cut -f1)
        local backup_time=$(stat -c %y "$backup_file" | cut -d' ' -f1-2)
        
        printf "%2d) %s (%s) - %s\n" $((i+1)) "$backup_date" "$backup_size" "$backup_time"
    done
    
    echo ""
}

# Function to extract backup
extract_backup() {
    local backup_file="$1"
    
    print_status "Extracting backup: $(basename "$backup_file")"
    
    # Create temporary restore directory
    rm -rf "$RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"
    
    # Extract backup
    tar -xzf "$backup_file" -C "$RESTORE_DIR"
    
    # Find extracted directory
    local extracted_dir=$(find "$RESTORE_DIR" -maxdepth 1 -type d -name "laso_backup_*" | head -1)
    
    if [[ -z "$extracted_dir" ]]; then
        print_error "Could not find extracted backup directory"
        return 1
    fi
    
    echo "$extracted_dir"
}

# Function to show backup manifest
show_manifest() {
    local backup_dir="$1"
    
    if [[ -f "$backup_dir/manifest.json" ]]; then
        print_status "Backup manifest:"
        cat "$backup_dir/manifest.json" | python3 -m json.tool 2>/dev/null || cat "$backup_dir/manifest.json"
        echo ""
    else
        print_warning "No manifest found in backup"
    fi
}

# Function to restore database
restore_database() {
    local backup_dir="$1"
    local force="$2"
    
    print_status "Restoring database..."
    
    # Check for SQLite database
    if [[ -f "$backup_dir/db.sqlite3" ]]; then
        if [[ -f "${PROJECT_ROOT}/db.sqlite3" ]] && [[ "$force" != "true" ]]; then
            print_warning "Existing SQLite database found. Use --force to overwrite."
            return 1
        fi
        
        cp "$backup_dir/db.sqlite3" "${PROJECT_ROOT}/db.sqlite3"
        print_success "SQLite database restored"
        return 0
    fi
    
    # Check for PostgreSQL database dump
    if [[ -f "$backup_dir/database.sql" ]]; then
        print_status "Restoring PostgreSQL database..."
        
        # Check if PostgreSQL container is running
        if ! docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" ps db | grep -q "Up"; then
            print_error "PostgreSQL container is not running. Please start it first."
            return 1
        fi
        
        # Load environment variables
        if [[ -f "${PROJECT_ROOT}/.env.prod" ]]; then
            set -a
            source "${PROJECT_ROOT}/.env.prod"
            set +a
        fi
        
        DB_NAME=${POSTGRES_DB:-laso_db}
        DB_USER=${POSTGRES_USER:-laso_user}
        
        if [[ "$force" != "true" ]]; then
            print_warning "This will overwrite the existing PostgreSQL database."
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Database restore cancelled"
                return 1
            fi
        fi
        
        # Drop and recreate database
        docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
        docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
        
        # Restore database
        docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db psql -U "$DB_USER" -d "$DB_NAME" < "$backup_dir/database.sql"
        
        print_success "PostgreSQL database restored"
        return 0
    fi
    
    print_warning "No database backup found"
}

# Function to restore media files
restore_media() {
    local backup_dir="$1"
    local force="$2"
    
    print_status "Restoring media files..."
    
    if [[ -f "$backup_dir/media.tar.gz" ]]; then
        if [[ -d "${PROJECT_ROOT}/media" ]] && [[ "$(ls -A "${PROJECT_ROOT}/media" 2>/dev/null)" ]] && [[ "$force" != "true" ]]; then
            print_warning "Existing media files found. Use --force to overwrite."
            return 1
        fi
        
        # Remove existing media directory
        rm -rf "${PROJECT_ROOT}/media"
        
        # Extract media files
        tar -xzf "$backup_dir/media.tar.gz" -C "$PROJECT_ROOT"
        
        print_success "Media files restored"
    else
        print_warning "No media backup found"
    fi
}

# Function to restore static files
restore_static() {
    local backup_dir="$1"
    local force="$2"
    
    print_status "Restoring static files..."
    
    if [[ -f "$backup_dir/staticfiles.tar.gz" ]]; then
        if [[ -d "${PROJECT_ROOT}/staticfiles" ]] && [[ "$(ls -A "${PROJECT_ROOT}/staticfiles" 2>/dev/null)" ]] && [[ "$force" != "true" ]]; then
            print_warning "Existing static files found. Use --force to overwrite."
            return 1
        fi
        
        # Remove existing static files directory
        rm -rf "${PROJECT_ROOT}/staticfiles"
        
        # Extract static files
        tar -xzf "$backup_dir/staticfiles.tar.gz" -C "$PROJECT_ROOT"
        
        print_success "Static files restored"
    else
        print_warning "No static files backup found"
    fi
}

# Function to restore configuration
restore_config() {
    local backup_dir="$1"
    local force="$2"
    
    print_status "Restoring configuration files..."
    
    # Restore Docker configuration
    if [[ -f "$backup_dir/docker-compose.prod.yml" ]]; then
        if [[ -f "${PROJECT_ROOT}/docker-compose.prod.yml" ]] && [[ "$force" != "true" ]]; then
            print_warning "Existing docker-compose.prod.yml found. Use --force to overwrite."
        else
            cp "$backup_dir/docker-compose.prod.yml" "${PROJECT_ROOT}/"
            print_success "Docker Compose configuration restored"
        fi
    fi
    
    # Restore Nginx configuration
    if [[ -d "$backup_dir/nginx" ]]; then
        if [[ -d "${PROJECT_ROOT}/deployment/nginx" ]] && [[ "$force" != "true" ]]; then
            print_warning "Existing nginx configuration found. Use --force to overwrite."
        else
            rm -rf "${PROJECT_ROOT}/deployment/nginx"
            cp -r "$backup_dir/nginx" "${PROJECT_ROOT}/deployment/"
            print_success "Nginx configuration restored"
        fi
    fi
}

# Function to cleanup temporary files
cleanup() {
    if [[ -d "$RESTORE_DIR" ]]; then
        rm -rf "$RESTORE_DIR"
        print_status "Temporary files cleaned up"
    fi
}

# Function to show help
show_help() {
    cat << EOF
LASO Digital Health - Restore Script

Usage: $0 [OPTIONS] [BACKUP_FILE]

Options:
  --list, -l           List available backups
  --force, -f          Force overwrite existing files
  --database-only      Restore only database
  --media-only         Restore only media files
  --config-only        Restore only configuration files
  --help, -h           Show this help message

Arguments:
  BACKUP_FILE          Path to backup file or backup number from --list

Examples:
  $0 --list                              # List available backups
  $0 1                                   # Restore backup #1 from list
  $0 /path/to/laso_backup_20240101.tar.gz  # Restore specific backup file
  $0 --database-only 1                   # Restore only database from backup #1
  $0 --force 1                           # Force restore backup #1

EOF
}

# Main restore function
main() {
    local backup_file=""
    local force=false
    local database_only=false
    local media_only=false
    local config_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --list|-l)
                list_backups
                exit 0
                ;;
            --force|-f)
                force=true
                shift
                ;;
            --database-only)
                database_only=true
                shift
                ;;
            --media-only)
                media_only=true
                shift
                ;;
            --config-only)
                config_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                backup_file="$1"
                shift
                ;;
        esac
    done
    
    # Check if backup file is specified
    if [[ -z "$backup_file" ]]; then
        print_error "No backup specified"
        print_status "Use --list to see available backups"
        exit 1
    fi
    
    # Handle backup selection by number
    if [[ "$backup_file" =~ ^[0-9]+$ ]]; then
        local backups=($(ls -1t "$BACKUP_DIR"/laso_backup_*.tar.gz 2>/dev/null || true))
        local backup_index=$((backup_file - 1))
        
        if [[ $backup_index -ge ${#backups[@]} ]] || [[ $backup_index -lt 0 ]]; then
            print_error "Invalid backup number: $backup_file"
            list_backups
            exit 1
        fi
        
        backup_file="${backups[$backup_index]}"
    fi
    
    # Check if backup file exists
    if [[ ! -f "$backup_file" ]]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_status "Starting restore from: $(basename "$backup_file")"
    
    # Extract backup
    local backup_dir
    backup_dir=$(extract_backup "$backup_file")
    
    # Show manifest
    show_manifest "$backup_dir"
    
    # Confirm restore operation
    if [[ "$force" != "true" ]]; then
        print_warning "This will restore data from the backup and may overwrite existing files."
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Restore cancelled"
            cleanup
            exit 0
        fi
    fi
    
    # Perform restore operations
    if [[ "$media_only" == "true" ]]; then
        restore_media "$backup_dir" "$force"
    elif [[ "$config_only" == "true" ]]; then
        restore_config "$backup_dir" "$force"
    elif [[ "$database_only" == "true" ]]; then
        restore_database "$backup_dir" "$force"
    else
        # Full restore
        restore_database "$backup_dir" "$force"
        restore_media "$backup_dir" "$force"
        restore_static "$backup_dir" "$force"
        restore_config "$backup_dir" "$force"
    fi
    
    # Cleanup
    cleanup
    
    print_success "Restore completed successfully!"
    print_status "You may need to restart your application containers"
    print_status "Run: ./run.sh prod"
}

# Error handling
trap 'print_error "Restore failed with error"; cleanup; exit 1' ERR

# Run main function
main "$@"
