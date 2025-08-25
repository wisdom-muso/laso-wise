#!/bin/bash

echo "🗄️  LASO Healthcare - SQLite Setup"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env file for SQLite..."
    
    # The .env file should already be created by the previous command
    if [ ! -f ".env" ]; then
        echo "❌ Failed to create .env file. Please create it manually."
        exit 1
    fi
fi

echo "✅ .env file found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing Python dependencies..."
if [ -f "requirements_sqlite.txt" ]; then
    pip install -r requirements_sqlite.txt
else
    pip install -r requirements.txt
fi

# Check if SQLite database exists
if [ ! -f "db.sqlite3" ]; then
    echo "🗄️  Creating SQLite database..."
else
    echo "✅ SQLite database found (db.sqlite3)"
fi

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Create admin user
echo "👤 Setting up admin user..."
python manage.py check_users

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "🎉 SQLite Setup Complete!"
echo "========================"
echo ""
echo "🚀 To start the server:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🌐 Access URLs:"
echo "   Application: http://65.108.91.110:8000/"
echo "   Admin Panel: http://65.108.91.110:8000/admin/"
echo "   Debug Auth:  http://65.108.91.110:8000/debug/auth/"
echo ""
echo "📁 Database File: db.sqlite3"
echo "💾 Backup this file to preserve your data!"
echo ""