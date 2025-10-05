#!/bin/bash

# Fix VPS Login Issue - Deployment Script
# This script fixes the login redirect issue on VPS deployments

echo "🔧 Fixing VPS Login Issue..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.production.example .env
    echo "⚠️  Please edit .env file with your actual configuration values!"
fi

# Ensure correct environment variables are set for HTTP deployment
echo "🔧 Setting up environment for HTTP deployment..."

# Update or add USE_HTTPS=False to .env file
if grep -q "USE_HTTPS=" .env; then
    sed -i 's/USE_HTTPS=.*/USE_HTTPS=False/' .env
else
    echo "USE_HTTPS=False" >> .env
fi

# Update or add DEBUG=False to .env file
if grep -q "DEBUG=" .env; then
    sed -i 's/DEBUG=.*/DEBUG=False/' .env
else
    echo "DEBUG=False" >> .env
fi

# Ensure SECRET_KEY is set
if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your-super-secret-key" .env; then
    echo "🔑 Generating new SECRET_KEY..."
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    if grep -q "SECRET_KEY=" .env; then
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    else
        echo "SECRET_KEY=$SECRET_KEY" >> .env
    fi
fi

echo "🐳 Rebuilding Docker containers..."

# Stop existing containers
docker-compose down

# Rebuild and start containers
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 30

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec web python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser if needed
echo "👤 Creating superuser (if needed)..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "✅ VPS Login Fix Complete!"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   http://65.108.91.110"
echo ""
echo "🔐 Default admin credentials (change immediately):"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Next steps:"
echo "   1. Test login functionality"
echo "   2. Change default admin password"
echo "   3. Configure your domain name if needed"
echo "   4. Set up SSL/HTTPS for production (optional)"
echo ""
echo "🔍 To check logs if issues persist:"
echo "   docker-compose logs web"
echo "   docker-compose logs nginx"