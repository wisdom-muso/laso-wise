#!/bin/bash

echo "🚀 Setting up LASO Healthcare users..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
elif [ -d "env" ]; then
    source env/bin/activate
    echo "✅ Virtual environment activated"
fi

# Check if Django is available
if ! python3 -c "import django" 2>/dev/null; then
    echo "❌ Django not found. Please install requirements first:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "📋 Checking current users..."
python3 manage.py check_users

echo ""
echo "🎯 If you need to create all sample data, run:"
echo "   python3 manage.py setup_laso_healthcare --all"
echo ""
echo "🔑 Default test credentials:"
echo "   Admin:   admin/admin123"
echo "   Doctor:  doctor/doctor123"  
echo "   Patient: patient/patient123"
echo ""
echo "✅ Setup complete!"