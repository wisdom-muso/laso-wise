#!/bin/bash

# Quick fix for registration issues on VPS 65.108.91.110
echo "🏥 Fixing registration issues for VPS 65.108.91.110..."

# Backup current .env
if [[ -f ".env" ]]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up current .env file"
fi

# Apply the correct environment configuration
cat > .env << 'EOF'
# LASO Healthcare - VPS Environment Configuration (65.108.91.110)
DEBUG=False
SECRET_KEY=hk$6b!2g*3q1o+0r@u4z#b@t@*j8=5f5+g3e#9ly2n^+%h5!z5
DJANGO_SETTINGS_MODULE=laso.settings
PYTHONPATH=/app

# Host Configuration - Your VPS IP
ALLOWED_HOSTS=65.108.91.110,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://65.108.91.110,https://65.108.91.110

# Database Configuration (PostgreSQL)
USE_SQLITE=False
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso2403
DATABASE_URL=postgresql://laso_user:laso2403@db:5432/laso_healthcare

# Redis Configuration
REDIS_PASSWORD=laso2403
REDIS_URL=redis://:laso2403@redis:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# Logging
LOG_TO_FILE=True

# AI Services (Optional)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Celery
CELERY_BROKER_URL=redis://:laso2403@redis:6379/0
CELERY_RESULT_BACKEND=redis://:laso2403@redis:6379/0
EOF

echo "✅ Applied VPS environment configuration"

# Restart the web container to apply changes
echo "🔄 Restarting web container..."
docker-compose -f docker-compose.production.yml restart web

# Wait for container to start
sleep 10

# Run migrations to ensure database is up to date
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate --noinput

# Test the registration endpoint
echo "🧪 Testing registration endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://65.108.91.110/core/patients/register/ || echo "000")
if [[ "$RESPONSE" == "200" ]]; then
    echo "✅ Registration endpoint is accessible"
else
    echo "⚠️  Registration endpoint returned HTTP $RESPONSE"
fi

echo ""
echo "🎉 Fix applied! Try registration again at:"
echo "   http://65.108.91.110/core/patients/register/"
echo ""
echo "💡 If you still get errors, check the logs:"
echo "   docker-compose -f docker-compose.production.yml logs web"