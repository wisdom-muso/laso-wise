#!/bin/bash

echo "🔧 Quick Fix: Restarting deployment with logging fixes"

# Check if .env exists, if not create it
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Database Configuration
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso_secure_password_123

# Redis Configuration
REDIS_PASSWORD=redis_secure_password_123

# Django Configuration
SECRET_KEY=django_secret_key_$(date +%s)_fixed
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# AI Configuration (optional)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=
EOF
fi

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="sudo docker-compose"
elif sudo docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="sudo docker compose"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true

echo "🏗️  Building and starting with fixes..."
$DOCKER_COMPOSE up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Checking service status..."
$DOCKER_COMPOSE ps

echo "🧪 Testing web application..."
if $DOCKER_COMPOSE logs web | grep -q "Booting worker"; then
    echo "✅ Web application is starting up"
    echo "🌐 Try accessing: http://localhost:8000"
else
    echo "❌ Web application may have issues. Checking logs..."
    $DOCKER_COMPOSE logs web --tail=20
fi

echo ""
echo "🔍 To view all logs: $DOCKER_COMPOSE logs -f"
echo "🛑 To stop: $DOCKER_COMPOSE down"