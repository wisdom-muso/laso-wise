.PHONY: help dev prod build up down logs clean ssl migrate superuser backup restore

# Default target
help:
	@echo "🐳 Laso Healthcare Docker Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-logs     - View development logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-logs    - View production logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make superuser    - Create Django superuser"
	@echo "  make backup       - Create database backup"
	@echo "  make restore      - Restore database from backup"
	@echo ""
	@echo "Utilities:"
	@echo "  make ssl          - Generate SSL certificates"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make logs         - View all logs"
	@echo "  make down         - Stop all containers"

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.dev.yml up --build

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Production commands
prod:
	docker-compose up -d

prod-build:
	docker-compose up -d --build

prod-logs:
	docker-compose logs -f

# Database commands
migrate:
	docker-compose exec web python manage.py migrate

superuser:
	docker-compose exec web python manage.py createsuperuser

backup:
	docker-compose exec db pg_dump -U laso_user laso_healthcare > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore:
	@echo "Usage: make restore BACKUP_FILE=your_backup_file.sql"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE"; exit 1; fi
	docker-compose exec -T db psql -U laso_user laso_healthcare < $(BACKUP_FILE)

# Utility commands
ssl:
	./scripts/generate-ssl.sh

clean:
	docker-compose down -v
	docker system prune -f
	@echo "Cleaned up containers and volumes"

logs:
	docker-compose logs

down:
	docker-compose down

# Health check
health:
	@echo "Checking application health..."
	@curl -f http://localhost:8000/health/ || echo "Health check failed"

# Setup commands
setup-dev: ssl dev-build
	@echo "Setting up development environment..."
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Running migrations..."
	@docker-compose -f docker-compose.dev.yml exec web python manage.py migrate || echo "Migrations failed - services may still be starting"
	@echo "Development environment ready!"
	@echo "Access the application at: http://localhost:8000"

setup-prod: ssl prod-build
	@echo "Setting up production environment..."
	@echo "Waiting for services to start..."
	@sleep 15
	@echo "Running migrations..."
	@docker-compose exec web python manage.py migrate || echo "Migrations failed - services may still be starting"
	@echo "Collecting static files..."
	@docker-compose exec web python manage.py collectstatic --noinput || echo "Static collection failed"
	@echo "Production environment ready!"
	@echo "Access the application at: https://localhost"