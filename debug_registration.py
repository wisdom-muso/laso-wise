#!/usr/bin/env python3
"""
LASO Healthcare - Registration Debug Script
This script helps diagnose registration issues on VPS deployment
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.forms import PatientRegistrationForm

User = get_user_model()

def test_database_connection():
    """Test database connectivity"""
    print("🔍 Testing database connection...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Database connection successful")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_model():
    """Test User model functionality"""
    print("\n🔍 Testing User model...")
    try:
        # Test user creation
        user_count = User.objects.count()
        print(f"✅ Current user count: {user_count}")
        
        # Test user fields
        user_fields = [f.name for f in User._meta.fields]
        required_fields = ['username', 'email', 'first_name', 'last_name', 'user_type']
        missing_fields = [field for field in required_fields if field not in user_fields]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required user fields present")
            return True
            
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_registration_form():
    """Test registration form validation"""
    print("\n🔍 Testing registration form...")
    
    # Test form with valid data
    valid_data = {
        'username': 'testuser123',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'date_of_birth': '1990-01-01',
        'phone_number': '+1234567890',
        'address': '123 Test Street',
        'gender': 'M',
        'blood_type': 'A+'
    }
    
    try:
        form = PatientRegistrationForm(data=valid_data)
        if form.is_valid():
            print("✅ Registration form validation passed")
            return True
        else:
            print("❌ Registration form validation failed:")
            for field, errors in form.errors.items():
                print(f"  - {field}: {', '.join(errors)}")
            return False
    except Exception as e:
        print(f"❌ Registration form test failed: {e}")
        return False

def test_existing_users():
    """Check for existing users that might cause conflicts"""
    print("\n🔍 Checking for existing users...")
    try:
        # Check for common test usernames
        test_usernames = ['admin', 'test', 'testuser', 'patient', 'doctor']
        existing_users = []
        
        for username in test_usernames:
            if User.objects.filter(username=username).exists():
                existing_users.append(username)
        
        if existing_users:
            print(f"⚠️  Found existing users: {', '.join(existing_users)}")
            print("   This might cause username conflicts during registration")
        else:
            print("✅ No conflicting usernames found")
            
        # Check for admin users
        admin_count = User.objects.filter(is_superuser=True).count()
        print(f"ℹ️  Admin users count: {admin_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ User check failed: {e}")
        return False

def test_csrf_settings():
    """Test CSRF configuration"""
    print("\n🔍 Testing CSRF settings...")
    try:
        csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        
        print(f"✅ ALLOWED_HOSTS: {allowed_hosts}")
        print(f"✅ CSRF_TRUSTED_ORIGINS: {csrf_trusted_origins}")
        
        if not allowed_hosts or allowed_hosts == ['*']:
            print("⚠️  ALLOWED_HOSTS is not properly configured")
            
        return True
        
    except Exception as e:
        print(f"❌ CSRF settings test failed: {e}")
        return False

def test_migrations():
    """Check migration status"""
    print("\n🔍 Checking migration status...")
    try:
        from django.core.management import execute_from_command_line
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connection
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print("❌ Pending migrations found:")
            for migration, backwards in plan:
                print(f"  - {migration}")
            return False
        else:
            print("✅ All migrations applied")
            return True
            
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🏥 LASO Healthcare - Registration Diagnostic Tool")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_user_model,
        test_migrations,
        test_existing_users,
        test_registration_form,
        test_csrf_settings,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 All tests passed! Registration should work correctly.")
    else:
        print(f"⚠️  {total - passed} out of {total} tests failed.")
        print("   Please address the issues above before testing registration.")
    
    print("\n💡 TROUBLESHOOTING TIPS:")
    print("1. Make sure all environment variables are set correctly")
    print("2. Ensure database migrations are applied: python manage.py migrate")
    print("3. Check that ALLOWED_HOSTS includes your VPS IP address")
    print("4. Verify CSRF_TRUSTED_ORIGINS includes your domain")
    print("5. Test registration with a unique username and email")
    
    print("\n🔗 REGISTRATION URL:")
    print("   Direct: http://your-vps-ip/core/patients/register/")
    print("   Redirect: http://your-vps-ip/register/")

if __name__ == '__main__':
    main()