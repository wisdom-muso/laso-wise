#!/usr/bin/env python3
"""
Debug script to identify login authentication issues
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model, authenticate
from django.contrib.sessions.models import Session
from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

User = get_user_model()

def test_database_connection():
    """Test database connectivity"""
    print("🔍 Testing database connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed - unexpected result")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_model():
    """Test user model and admin user"""
    print("\n🔍 Testing user model...")
    try:
        # Check if admin user exists
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            print(f"✅ Admin user found: {admin_user.username}")
            print(f"   - Email: {admin_user.email}")
            print(f"   - Is active: {admin_user.is_active}")
            print(f"   - Is staff: {admin_user.is_staff}")
            print(f"   - Is superuser: {admin_user.is_superuser}")
            print(f"   - Last login: {admin_user.last_login}")
            return admin_user
        else:
            print("❌ Admin user not found")
            return None
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return None

def test_authentication():
    """Test authentication with admin credentials"""
    print("\n🔍 Testing authentication...")
    try:
        # Test authentication with admin credentials
        user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
        if user:
            print(f"✅ Authentication successful for user: {user.username}")
            return True
        else:
            print("❌ Authentication failed - invalid credentials or authentication backend issue")
            
            # Try to check if user exists but password is wrong
            admin_user = User.objects.filter(username='admin').first()
            if admin_user:
                print("   - Admin user exists, but password authentication failed")
                print("   - This could be a password hash issue")
            else:
                print("   - Admin user does not exist")
            return False
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_session_configuration():
    """Test session configuration"""
    print("\n🔍 Testing session configuration...")
    try:
        print(f"Session engine: {settings.SESSION_ENGINE}")
        print(f"Session cookie age: {settings.SESSION_COOKIE_AGE}")
        print(f"Session cookie secure: {getattr(settings, 'SESSION_COOKIE_SECURE', 'Not set')}")
        print(f"Session cookie httponly: {getattr(settings, 'SESSION_COOKIE_HTTPONLY', 'Not set')}")
        print(f"Session cookie samesite: {getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Not set')}")
        
        # Test session model if using database sessions
        if 'database' in settings.SESSION_ENGINE:
            session_count = Session.objects.count()
            print(f"Active sessions in database: {session_count}")
        
        print("✅ Session configuration checked")
        return True
    except Exception as e:
        print(f"❌ Session configuration test failed: {e}")
        return False

def test_middleware():
    """Test middleware configuration"""
    print("\n🔍 Testing middleware configuration...")
    try:
        middleware = settings.MIDDLEWARE
        required_middleware = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
        ]
        
        for mw in required_middleware:
            if mw in middleware:
                print(f"✅ {mw} - Found")
            else:
                print(f"❌ {mw} - Missing")
        
        print("✅ Middleware configuration checked")
        return True
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        return False

def test_authentication_backends():
    """Test authentication backends"""
    print("\n🔍 Testing authentication backends...")
    try:
        backends = getattr(settings, 'AUTHENTICATION_BACKENDS', ['django.contrib.auth.backends.ModelBackend'])
        print(f"Authentication backends: {backends}")
        
        for backend in backends:
            print(f"✅ Backend: {backend}")
        
        return True
    except Exception as e:
        print(f"❌ Authentication backends test failed: {e}")
        return False

def check_password_hash():
    """Check if admin user password hash is correct"""
    print("\n🔍 Checking admin user password hash...")
    try:
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            print(f"Password hash: {admin_user.password[:50]}...")
            
            # Check if password is properly hashed
            if admin_user.password.startswith('pbkdf2_sha256$') or admin_user.password.startswith('argon2$'):
                print("✅ Password appears to be properly hashed")
                
                # Test password verification
                if admin_user.check_password('8gJW48Tz8YXDrF57'):
                    print("✅ Password verification successful")
                    return True
                else:
                    print("❌ Password verification failed")
                    return False
            else:
                print("❌ Password does not appear to be properly hashed")
                return False
        else:
            print("❌ Admin user not found")
            return False
    except Exception as e:
        print(f"❌ Password hash check failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🚀 LASO Healthcare Login Diagnostic Tool")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("User Model", test_user_model),
        ("Authentication", test_authentication),
        ("Session Configuration", test_session_configuration),
        ("Middleware", test_middleware),
        ("Authentication Backends", test_authentication_backends),
        ("Password Hash", check_password_hash),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not results.get("Database Connection"):
            print("- Check database connection and credentials")
        if not results.get("User Model"):
            print("- Recreate admin user or check user model")
        if not results.get("Authentication"):
            print("- Check authentication backends and user credentials")
        if not results.get("Password Hash"):
            print("- Reset admin user password")
    else:
        print("\n🎉 All tests passed! The issue might be in the frontend or session handling.")

if __name__ == '__main__':
    main()