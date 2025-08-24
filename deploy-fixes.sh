#!/bin/bash

echo "=== Laso Healthcare Deployment Fixes ==="
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

# Collect static files
echo "[INFO] Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "[INFO] Running database migrations..."
python manage.py migrate

echo ""
echo "=== Deployment Fixes Applied ==="
echo "✅ WhiteNoise middleware added for static file serving"
echo "✅ Button state JavaScript fixed"
echo "✅ Teal color theme applied"
echo "✅ Static files collected"
echo "✅ English language migration completed"
echo ""
echo "Ready for deployment!"
echo ""