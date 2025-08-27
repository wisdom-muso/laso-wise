#!/bin/bash

echo "🧹 Removing demo data from Laso Healthcare..."

# Check if containers are running
if ! docker-compose ps | grep -q "laso_web.*Up"; then
    echo "❌ Docker containers are not running. Start them first with:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "⚠️  This will remove all demo/sample data including:"
echo "   - Sample users (except admin)"
echo "   - Sample appointments"
echo "   - Sample treatments"
echo "   - Sample notifications"
echo "   - Sample messages"
echo ""

read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo "🚀 Executing cleanup..."

# Run the cleanup command
docker-compose exec web python manage.py cleanup_demo_data --confirm

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Demo data cleanup completed successfully!"
    echo ""
    echo "🔧 System is now clean for production use"
    echo "📝 You can now add real users and data through the admin interface"
else
    echo ""
    echo "❌ Cleanup failed. Check the logs for details:"
    echo "   docker-compose logs web"
fi