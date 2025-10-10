#!/usr/bin/env python3
"""
Reset database and recreate users for LASO Healthcare System
This script will completely reset user data and recreate admin with new credentials
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
from django.core.management import execute_from_command_line

User = get_user_model()

def check_current_admin():
    """Check what admin users currently exist"""
    print("🔍 Checking current admin users...")
    try:
        admin_users = User.objects.filter(is_superuser=True)
        print(f"Found {admin_users.count()} admin users:")
        for user in admin_users:
            print(f"  - Username: {user.username}")
            print(f"    Email: {user.email}")
            print(f"    Is active: {user.is_active}")
            print(f"    Date joined: {user.date_joined}")
            print(f"    Last login: {user.last_login}")
            print(f"    Password hash: {user.password[:50]}...")
            print()
        return admin_users
    except Exception as e:
        print(f"❌ Failed to check admin users: {e}")
        return None

def test_old_credentials():
    """Test if old admin credentials still work"""
    print("🔐 Testing old admin credentials...")
    try:
        from django.contrib.auth import authenticate
        
        # Try old credentials
        old_passwords = ['admin123', 'admin', 'password', 'laso123', 'healthcare123']
        
        for password in old_passwords:
            user = authenticate(username='admin', password=password)
            if user:
                print(f"✅ Old password '{password}' still works!")
                return password
        
        print("❌ None of the common old passwords work")
        return None
    except Exception as e:
        print(f"❌ Failed to test old credentials: {e}")
        return None

def completely_reset_users():
    """Completely delete all users and start fresh"""
    print("🗑️  Completely resetting all users...")
    try:
        with transaction.atomic():
            # Get count before deletion
            user_count = User.objects.count()
            print(f"Found {user_count} users to delete")
            
            # Delete all users
            User.objects.all().delete()
            print("✅ All users deleted")
            
            # Clear all sessions
            session_count = Session.objects.count()
            Session.objects.all().delete()
            print(f"✅ Cleared {session_count} sessions")
            
        return True
    except Exception as e:
        print(f"❌ Failed to reset users: {e}")
        return False

def create_fresh_admin():
    """Create a completely fresh admin user"""
    print("👤 Creating fresh admin user...")
    try:
        # Create new admin user with the credentials we want
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@laso.com',
            password='8gJW48Tz8YXDrF57',
            first_name='System',
            last_name='Administrator'
        )
        
        print(f"✅ Fresh admin user created: {admin_user.username}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - Password: 8gJW48Tz8YXDrF57")
        print(f"   - Is active: {admin_user.is_active}")
        print(f"   - Is staff: {admin_user.is_staff}")
        print(f"   - Is superuser: {admin_user.is_superuser}")
        print(f"   - Password hash: {admin_user.password[:50]}...")
        
        return admin_user
    except Exception as e:
        print(f"❌ Failed to create fresh admin: {e}")
        return None

def create_fresh_patient():
    """Create a fresh test patient user"""
    print("🏥 Creating fresh test patient...")
    try:
        patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpatient123',
            first_name='Test',
            last_name='Patient',
            user_type='patient'
        )
        
        print(f"✅ Fresh patient user created: {patient_user.username}")
        print(f"   - Email: {patient_user.email}")
        print(f"   - Password: testpatient123")
        print(f"   - User type: {patient_user.user_type}")
        
        return patient_user
    except Exception as e:
        print(f"❌ Failed to create fresh patient: {e}")
        return None

def verify_new_credentials():
    """Verify the new credentials work"""
    print("✅ Verifying new credentials...")
    try:
        from django.contrib.auth import authenticate
        
        # Test new admin credentials
        admin_user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
        if admin_user:
            print("✅ New admin credentials work!")
        else:
            print("❌ New admin credentials failed!")
            return False
        
        # Test new patient credentials
        patient_user = authenticate(username='patient', password='testpatient123')
        if patient_user:
            print("✅ New patient credentials work!")
        else:
            print("❌ New patient credentials failed!")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Credential verification failed: {e}")
        return False

def reset_database_migrations():
    """Reset database migrations to ensure clean state"""
    print("🔄 Resetting database migrations...")
    try:
        # Run migrations to ensure all tables are properly created
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Database migrations completed")
        return True
    except Exception as e:
        print(f"❌ Migration reset failed: {e}")
        return False

def main():
    """Run complete database and user reset"""
    print("🔄 LASO Healthcare Database and User Reset")
    print("=" * 60)
    
    # Step 1: Check current state
    print("\n📊 STEP 1: Analyzing current state")
    current_admins = check_current_admin()
    old_password = test_old_credentials()
    
    if old_password:
        print(f"⚠️  WARNING: Old password '{old_password}' is still active!")
        print("This confirms the database is retaining old user data.")
    
    # Step 2: Reset database migrations
    print("\n🔄 STEP 2: Resetting database migrations")
    if not reset_database_migrations():
        print("❌ Failed to reset migrations. Continuing anyway...")
    
    # Step 3: Completely reset users
    print("\n🗑️  STEP 3: Completely resetting all users")
    if not completely_reset_users():
        print("❌ Failed to reset users. Aborting.")
        return False
    
    # Step 4: Create fresh admin
    print("\n👤 STEP 4: Creating fresh admin user")
    admin_user = create_fresh_admin()
    if not admin_user:
        print("❌ Failed to create admin. Aborting.")
        return False
    
    # Step 5: Create fresh patient
    print("\n🏥 STEP 5: Creating fresh test patient")
    patient_user = create_fresh_patient()
    if not patient_user:
        print("⚠️  Failed to create patient, but continuing...")
    
    # Step 6: Verify new credentials
    print("\n✅ STEP 6: Verifying new credentials")
    if not verify_new_credentials():
        print("❌ Credential verification failed!")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE AND USER RESET COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n🔑 NEW LOGIN CREDENTIALS:")
    print("Admin Login:")
    print("  URL: http://65.108.91.110/admin/")
    print("  Username: admin")
    print("  Password: 8gJW48Tz8YXDrF57")
    print("\nPatient Login:")
    print("  URL: http://65.108.91.110/login/")
    print("  Username: patient")
    print("  Password: testpatient123")
    
    print("\n⚠️  IMPORTANT: The old admin credentials should no longer work!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)