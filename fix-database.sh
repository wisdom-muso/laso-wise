#!/bin/bash

# LASO Healthcare - Database Connection Fix Script
# This script fixes the database connection issue in your deployment

set -e

echo "🔧 LASO Healthcare - Database Connection Fix"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

echo ""
echo "📊 Current container status:"
docker-compose ps

echo ""
echo "🔍 Checking database service..."

# Check if PostgreSQL container exists and is running
if docker-compose ps db | grep -q "Up"; then
    echo "✅ PostgreSQL database service is running"
    echo ""
    echo "🔄 Running database migrations..."
    docker-compose exec web python manage.py migrate
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ PostgreSQL database service is not running"
    echo ""
    echo "Choose a solution:"
    echo "1. Start PostgreSQL service (recommended for production)"
    echo "2. Switch to SQLite (simpler, good for single-server setups)"
    echo ""
    read -p "Enter your choice (1 or 2): " choice
    
    case $choice in
        1)
            echo ""
            echo "🚀 Starting PostgreSQL database service..."
            docker-compose up -d db
            
            echo "⏳ Waiting for database to be ready..."
            sleep 10
            
            # Wait for database to be healthy
            echo "🔄 Checking database health..."
            timeout=60
            while [ $timeout -gt 0 ]; do
                if docker-compose ps db | grep -q "healthy"; then
                    echo "✅ Database is healthy!"
                    break
                fi
                echo "⏳ Waiting for database... ($timeout seconds remaining)"
                sleep 5
                timeout=$((timeout - 5))
            done
            
            if [ $timeout -le 0 ]; then
                echo "❌ Database failed to start within 60 seconds"
                echo "📋 Database logs:"
                docker-compose logs db
                exit 1
            fi
            
            echo ""
            echo "🔄 Running database migrations..."
            docker-compose exec web python manage.py migrate
            echo "✅ Database migrations completed successfully!"
            ;;
        2)
            echo ""
            echo "🔄 Switching to SQLite database..."
            
            # Stop all services
            echo "⏹️  Stopping all services..."
            docker-compose down
            
            # Create or update .env file to use SQLite
            if [ -f ".env" ]; then
                # Update existing .env file
                if grep -q "USE_SQLITE" .env; then
                    sed -i 's/USE_SQLITE=.*/USE_SQLITE=True/' .env
                else
                    echo "USE_SQLITE=True" >> .env
                fi
            else
                # Create new .env file
                echo "USE_SQLITE=True" > .env
            fi
            
            echo "✅ Updated configuration to use SQLite"
            
            # Start services without database dependency
            echo "🚀 Starting services with SQLite..."
            docker-compose up -d web redis celery celery-beat nginx
            
            echo "⏳ Waiting for web service to be ready..."
            sleep 10
            
            echo "🔄 Running database migrations with SQLite..."
            docker-compose exec web python manage.py migrate
            echo "✅ Database migrations completed successfully!"
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

echo ""
echo "🎉 Database connection issue fixed!"
echo ""
echo "📊 Final container status:"
docker-compose ps

echo ""
echo "🌐 Your application should now be accessible at:"
echo "   • Main application: http://65.108.91.110:3000"
echo "   • Nginx proxy: http://65.108.91.110:8081"
echo ""
echo "✅ Database fix completed successfully!"