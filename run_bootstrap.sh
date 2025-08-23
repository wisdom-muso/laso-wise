#!/bin/bash

# Script to run Django Bootstrap UI on port 8005
echo "Starting Laso Digital Health Bootstrap UI..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=laso.settings
export DEBUG=True
export SECRET_KEY=g!y0otek@9t^b+b*7)&q2a5^=8_9&xcdii8@6h^_*wphl-\(fu9
export ALLOWED_HOSTS=*,localhost,127.0.0.1,0.0.0.0
export CSRF_TRUSTED_ORIGINS=http://localhost:8005,http://127.0.0.1:8005,http://localhost:3000,http://127.0.0.1:3000

# Check if we can run with minimal dependencies
echo "Installing minimal dependencies..."
python3 -m pip install django python-dotenv dj-database-url --break-system-packages --quiet 2>/dev/null || echo "Dependencies already installed"

# Run migrations (if needed)
echo "Running migrations..."
python3 manage.py migrate --run-syncdb 2>/dev/null || echo "Using existing database"

# Create superuser if needed
echo "Checking for admin user..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123')
    print('Created admin user: admin/admin123')
else:
    print('Admin user already exists')
" 2>/dev/null

# Start the server
echo "Starting Django server on port 8005..."
echo "Bootstrap UI will be available at: http://localhost:8005/"
echo "Admin interface: http://localhost:8005/admin/"
echo "Custom dashboard: http://localhost:8005/dashboard/"
echo ""
echo "Default login credentials:"
echo "Username: admin"
echo "Password: admin123"
echo ""

python3 manage.py runserver 0.0.0.0:8005