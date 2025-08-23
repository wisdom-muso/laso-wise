#!/bin/bash

# =============================================================================
# Laso Healthcare Docker Startup Script
# =============================================================================

set -e  # Exit on any error

echo "🏥 Starting Laso Healthcare Docker Environment..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values!"
    echo "   Required: SECRET_KEY, database passwords, email settings"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs backups docker/nginx/ssl

# Generate a random secret key if not set
if grep -q "your-very-long-random-secret-key" .env; then
    echo "🔑 Generating random SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    sed -i "s/your-very-long-random-secret-key-here-min-50-characters-long/$SECRET_KEY/" .env
fi

# Build the application
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Start the services
echo "🚀 Starting services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T db psql -U ${POSTGRES_USER:-laso_user} -d ${POSTGRES_DB:-laso_healthcare} -c "SELECT 1;" > /dev/null 2>&1
docker-compose run --rm web python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
docker-compose run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso-healthcare.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Load initial data if setup command exists
echo "📋 Loading initial data..."
if docker-compose run --rm web python manage.py help | grep -q "setup_laso_healthcare"; then
    docker-compose run --rm web python manage.py setup_laso_healthcare --sample-data
else
    echo "⚠️  setup_laso_healthcare command not found, skipping sample data"
fi

# Start all services
echo "🌟 Starting all services..."
docker-compose up -d

# Show status
echo ""
echo "✅ Laso Healthcare is starting up!"
echo "=================================================="
echo "🌐 Application: http://localhost"
echo "👨‍💼 Admin Panel: http://localhost/admin"
echo "📊 Health Check: http://localhost/health"
echo ""
echo "Default login credentials:"
echo "- Username: admin"
echo "- Password: admin123"
echo ""
echo "🔍 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo "📈 To view status: docker-compose ps"
echo ""

# Wait a moment and check service health
sleep 5
echo "Service Status:"
docker-compose ps