#!/bin/bash

# =============================================================================
# Laso Healthcare Docker Management Script
# =============================================================================

set -e

COMMAND=${1:-help}

show_help() {
    echo "🏥 Laso Healthcare Docker Management"
    echo "===================================="
    echo ""
    echo "Usage: ./docker-manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start all services"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  status        Show service status"
    echo "  logs          Show application logs"
    echo "  logs-f        Follow application logs"
    echo "  shell         Open Django shell"
    echo "  bash          Open bash shell in web container"
    echo "  migrate       Run database migrations"
    echo "  makemigrations Create new migrations"
    echo "  collectstatic Collect static files"
    echo "  createsuperuser Create admin user"
    echo "  backup        Create database backup"
    echo "  restore       Restore database from backup"
    echo "  clean         Clean up containers and volumes"
    echo "  rebuild       Rebuild and restart services"
    echo "  update        Pull latest code and restart"
    echo "  health        Check service health"
    echo "  help          Show this help message"
    echo ""
}

case $COMMAND in
    start)
        echo "🚀 Starting Laso Healthcare services..."
        docker-compose up -d
        echo "✅ Services started!"
        docker-compose ps
        ;;
    
    stop)
        echo "🛑 Stopping Laso Healthcare services..."
        docker-compose down
        echo "✅ Services stopped!"
        ;;
    
    restart)
        echo "🔄 Restarting Laso Healthcare services..."
        docker-compose restart
        echo "✅ Services restarted!"
        docker-compose ps
        ;;
    
    status)
        echo "📊 Service Status:"
        docker-compose ps
        echo ""
        echo "📈 Container Stats:"
        docker stats --no-stream
        ;;
    
    logs)
        echo "📋 Application logs (last 100 lines):"
        docker-compose logs --tail=100 web
        ;;
    
    logs-f)
        echo "📋 Following application logs (Ctrl+C to exit):"
        docker-compose logs -f web
        ;;
    
    shell)
        echo "🐍 Opening Django shell..."
        docker-compose exec web python manage.py shell
        ;;
    
    bash)
        echo "💻 Opening bash shell..."
        docker-compose exec web bash
        ;;
    
    migrate)
        echo "🗄️  Running database migrations..."
        docker-compose exec web python manage.py migrate
        echo "✅ Migrations completed!"
        ;;
    
    makemigrations)
        echo "📝 Creating new migrations..."
        docker-compose exec web python manage.py makemigrations
        echo "✅ Migrations created!"
        ;;
    
    collectstatic)
        echo "📦 Collecting static files..."
        docker-compose exec web python manage.py collectstatic --noinput
        echo "✅ Static files collected!"
        ;;
    
    createsuperuser)
        echo "👤 Creating superuser..."
        docker-compose exec web python manage.py createsuperuser
        ;;
    
    backup)
        echo "💾 Creating database backup..."
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        docker-compose exec -T db pg_dump -U ${POSTGRES_USER:-laso_user} ${POSTGRES_DB:-laso_healthcare} > "./backups/$BACKUP_FILE"
        echo "✅ Backup created: ./backups/$BACKUP_FILE"
        ;;
    
    restore)
        if [ -z "$2" ]; then
            echo "❌ Please specify backup file:"
            echo "   ./docker-manage.sh restore backup_file.sql"
            ls -la ./backups/ 2>/dev/null || echo "No backups found in ./backups/"
            exit 1
        fi
        echo "🔄 Restoring database from $2..."
        cat "./backups/$2" | docker-compose exec -T db psql -U ${POSTGRES_USER:-laso_user} -d ${POSTGRES_DB:-laso_healthcare}
        echo "✅ Database restored!"
        ;;
    
    clean)
        echo "🧹 Cleaning up Docker resources..."
        read -p "This will remove all containers, volumes, and images. Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker system prune -f
            docker volume prune -f
            echo "✅ Cleanup completed!"
        else
            echo "❌ Cleanup cancelled."
        fi
        ;;
    
    rebuild)
        echo "🔨 Rebuilding and restarting services..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Services rebuilt and restarted!"
        docker-compose ps
        ;;
    
    update)
        echo "📥 Pulling latest code and restarting..."
        git pull
        docker-compose down
        docker-compose build
        docker-compose up -d
        docker-compose exec web python manage.py migrate
        docker-compose exec web python manage.py collectstatic --noinput
        echo "✅ Update completed!"
        ;;
    
    health)
        echo "🔍 Checking service health..."
        echo ""
        echo "Database:"
        docker-compose exec db pg_isready -U ${POSTGRES_USER:-laso_user} || echo "❌ Database not ready"
        echo ""
        echo "Redis:"
        docker-compose exec redis redis-cli ping || echo "❌ Redis not ready"
        echo ""
        echo "Web Application:"
        curl -f http://localhost/health/ > /dev/null 2>&1 && echo "✅ Web app healthy" || echo "❌ Web app not responding"
        echo ""
        echo "Services:"
        docker-compose ps
        ;;
    
    help|*)
        show_help
        ;;
esac