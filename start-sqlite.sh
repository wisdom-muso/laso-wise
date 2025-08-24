#!/bin/bash

echo "=== Laso Healthcare SQLite Setup ==="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[INFO] Installing requirements..."
pip install -r requirements_sqlite.txt

# Run migrations
echo "[INFO] Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "[INFO] Creating superuser (if needed)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123')
    print("Superuser created: admin/admin123")
else:
    print("Superuser already exists")
EOF

# Collect static files
echo "[INFO] Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=== Setup Complete ==="
echo "You can now run: python manage.py runserver"
echo "Admin login: admin / admin123"
echo "Access at: http://localhost:8000"
echo ""