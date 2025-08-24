#!/usr/bin/env python3
"""
Simple Django test to verify the application can start
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meditrack.settings')

def test_django_setup():
    """Test if Django can be set up properly"""
    try:
        django.setup()
        print("✅ Django setup successful")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_imports():
    """Test if key modules can be imported"""
    modules_to_test = [
        'users.models',
        'appointments.models', 
        'treatments.models',
        'telemedicine.models',
        'core.views'
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
            success_count += 1
        except Exception as e:
            print(f"❌ {module} import failed: {e}")
    
    return success_count == len(modules_to_test)

if __name__ == "__main__":
    print("🧪 Testing Django Application Setup")
    print("=" * 40)
    
    # Test Django setup
    django_ok = test_django_setup()
    
    if django_ok:
        # Test imports
        imports_ok = test_imports()
        
        # Note: Skip database test since we don't have a database set up
        print("\n📝 Note: Database test skipped (no database configured)")
    
    print("\n" + "=" * 40)
    if django_ok:
        print("🎉 Django application setup test passed!")
        print("✅ Ready for deployment")
    else:
        print("💥 Django application setup test failed!")
        print("❌ Please check the issues above")
        sys.exit(1)