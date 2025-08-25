#!/usr/bin/env python3
"""
SQLite Configuration Verification Script
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meditrack.settings')

try:
    django.setup()
    
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db import connection
    
    print("🔍 SQLite Configuration Verification")
    print("=" * 40)
    
    # Check database configuration
    db_config = settings.DATABASES['default']
    print(f"📁 Database Engine: {db_config['ENGINE']}")
    print(f"📁 Database Name: {db_config['NAME']}")
    
    # Check if using SQLite
    if 'sqlite3' in db_config['ENGINE']:
        print("✅ SQLite is correctly configured!")
        
        # Check if database file exists
        db_path = db_config['NAME']
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            
            # Get file size
            size = os.path.getsize(db_path)
            print(f"📊 Database size: {size:,} bytes ({size/1024:.1f} KB)")
        else:
            print(f"⚠️  Database file not found: {db_path}")
            print("   Run 'python manage.py migrate' to create it")
    else:
        print("❌ Not using SQLite!")
        print(f"   Current engine: {db_config['ENGINE']}")
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]
            print(f"✅ Connection successful! Found {table_count} tables")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    # Check users
    print("\n👥 User Information:")
    try:
        User = get_user_model()
        user_count = User.objects.count()
        print(f"📊 Total users: {user_count}")
        
        if user_count > 0:
            print("👤 Sample users:")
            for user in User.objects.all()[:5]:
                print(f"   - {user.username} ({user.email}) - {user.user_type}")
            if user_count > 5:
                print(f"   ... and {user_count - 5} more users")
        else:
            print("⚠️  No users found. Create users with:")
            print("   python manage.py createsuperuser")
            print("   or")
            print("   python manage.py check_users")
    except Exception as e:
        print(f"❌ User query failed: {e}")
    
    # Environment check
    print(f"\n🔧 Environment Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   USE_SQLITE: {getattr(settings, 'USE_SQLITE', 'Not set')}")
    print(f"   SECRET_KEY: {'Set' if settings.SECRET_KEY else 'Not set'}")
    
    print("\n✅ SQLite verification complete!")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
    import traceback
    traceback.print_exc()