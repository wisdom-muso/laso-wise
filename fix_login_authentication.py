#!/usr/bin/env python3
"""
Fix login authentication issues in LASO Healthcare System
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

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.conf import settings
from django.db import connection, transaction

User = get_user_model()

def clear_all_sessions():
    """Clear all existing sessions to fix any corrupted session data"""
    print("🧹 Clearing all existing sessions...")
    try:
        session_count = Session.objects.count()
        Session.objects.all().delete()
        print(f"✅ Cleared {session_count} sessions")
        return True
    except Exception as e:
        print(f"❌ Failed to clear sessions: {e}")
        return False

def recreate_admin_user():
    """Recreate admin user with proper password hash"""
    print("👤 Recreating admin user...")
    try:
        # Delete existing admin user if exists
        User.objects.filter(username='admin').delete()
        
        # Create new admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@laso.com',
            password='8gJW48Tz8YXDrF57',
            first_name='Admin',
            last_name='User'
        )
        
        print(f"✅ Admin user created successfully: {admin_user.username}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - Is active: {admin_user.is_active}")
        print(f"   - Is staff: {admin_user.is_staff}")
        print(f"   - Is superuser: {admin_user.is_superuser}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to recreate admin user: {e}")
        return False

def create_test_patient():
    """Create a test patient user for testing"""
    print("🏥 Creating test patient user...")
    try:
        # Delete existing test patient if exists
        User.objects.filter(username='patient').delete()
        
        # Create test patient user
        patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpatient123',
            first_name='Test',
            last_name='Patient',
            user_type='patient'
        )
        
        print(f"✅ Test patient created successfully: {patient_user.username}")
        print(f"   - Email: {patient_user.email}")
        print(f"   - User type: {patient_user.user_type}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create test patient: {e}")
        return False

def test_authentication():
    """Test authentication with recreated users"""
    print("🔐 Testing authentication...")
    try:
        from django.contrib.auth import authenticate
        
        # Test admin authentication
        admin_user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
        if admin_user:
            print("✅ Admin authentication successful")
        else:
            print("❌ Admin authentication failed")
            return False
        
        # Test patient authentication
        patient_user = authenticate(username='patient', password='testpatient123')
        if patient_user:
            print("✅ Patient authentication successful")
        else:
            print("❌ Patient authentication failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def run_migrations():
    """Run database migrations to ensure all tables are up to date"""
    print("🔄 Running database migrations...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Database migrations completed")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Run all fixes"""
    print("🔧 LASO Healthcare Login Authentication Fix")
    print("=" * 50)
    
    fixes = [
        ("Database Migrations", run_migrations),
        ("Clear Sessions", clear_all_sessions),
        ("Recreate Admin User", recreate_admin_user),
        ("Create Test Patient", create_test_patient),
        ("Test Authentication", test_authentication),
    ]
    
    results = {}
    for fix_name, fix_func in fixes:
        try:
            print(f"\n🔧 {fix_name}...")
            results[fix_name] = fix_func()
        except Exception as e:
            print(f"❌ {fix_name} failed: {e}")
            results[fix_name] = False
    
    print("\n" + "=" * 50)
    print("📊 FIX SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for fix_name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{fix_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} successful, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All fixes applied successfully!")
        print("\n📝 LOGIN CREDENTIALS:")
        print("Admin Login:")
        print("  Username: admin")
        print("  Password: 8gJW48Tz8YXDrF57")
        print("  URL: http://65.108.91.110/admin/")
        print("\nPatient Login:")
        print("  Username: patient")
        print("  Password: testpatient123")
        print("  URL: http://65.108.91.110/login/")
    else:
        print(f"\n⚠️  {failed} fixes failed. Please check the errors above.")

if __name__ == '__main__':
    main()