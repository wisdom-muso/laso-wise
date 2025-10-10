#!/usr/bin/env python3
"""
Check current admin credentials in the database
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

User = get_user_model()

def check_admin_users():
    """Check all admin users in the database"""
    print("🔍 Checking all admin users in database...")
    try:
        admin_users = User.objects.filter(is_superuser=True)
        print(f"Found {admin_users.count()} admin users:")
        
        for user in admin_users:
            print(f"\n👤 Admin User: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - Is active: {user.is_active}")
            print(f"   - Is staff: {user.is_staff}")
            print(f"   - Is superuser: {user.is_superuser}")
            print(f"   - Date joined: {user.date_joined}")
            print(f"   - Last login: {user.last_login}")
            print(f"   - Password hash: {user.password[:50]}...")
            
        return admin_users
    except Exception as e:
        print(f"❌ Failed to check admin users: {e}")
        return []

def test_common_passwords():
    """Test common admin passwords"""
    print("\n🔐 Testing common admin passwords...")
    
    common_passwords = [
        '8gJW48Tz8YXDrF57',  # New password
        'admin123',
        'admin',
        'password',
        'laso123',
        'healthcare123',
        'laso_admin',
        'admin2024',
        'password123',
        '123456',
        'root',
        'administrator'
    ]
    
    working_passwords = []
    
    for password in common_passwords:
        try:
            user = authenticate(username='admin', password=password)
            if user:
                print(f"✅ Password '{password}' WORKS!")
                working_passwords.append(password)
            else:
                print(f"❌ Password '{password}' failed")
        except Exception as e:
            print(f"⚠️  Error testing password '{password}': {e}")
    
    return working_passwords

def check_all_users():
    """Check all users in the database"""
    print("\n👥 Checking all users in database...")
    try:
        all_users = User.objects.all()
        print(f"Total users in database: {all_users.count()}")
        
        for user in all_users:
            user_type = getattr(user, 'user_type', 'unknown')
            print(f"  - {user.username} ({user.email}) - Type: {user_type} - Active: {user.is_active}")
            
        return all_users
    except Exception as e:
        print(f"❌ Failed to check all users: {e}")
        return []

def main():
    """Run all checks"""
    print("🔍 LASO Healthcare Admin Credentials Check")
    print("=" * 50)
    
    # Check admin users
    admin_users = check_admin_users()
    
    # Test passwords
    working_passwords = test_common_passwords()
    
    # Check all users
    all_users = check_all_users()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    print(f"Total admin users: {len(admin_users)}")
    print(f"Total users: {len(all_users)}")
    print(f"Working passwords found: {len(working_passwords)}")
    
    if working_passwords:
        print("\n🔑 WORKING ADMIN CREDENTIALS:")
        for password in working_passwords:
            print(f"  Username: admin")
            print(f"  Password: {password}")
            print()
    else:
        print("\n❌ No working admin passwords found!")
    
    if len(working_passwords) > 1:
        print("⚠️  WARNING: Multiple passwords work! This suggests database inconsistency.")
        print("   Recommendation: Run complete database reset.")
    elif len(working_passwords) == 1 and working_passwords[0] != '8gJW48Tz8YXDrF57':
        print("⚠️  WARNING: Old password still works instead of new one!")
        print("   Recommendation: Run complete database reset.")
    elif len(working_passwords) == 1 and working_passwords[0] == '8gJW48Tz8YXDrF57':
        print("✅ Perfect! Only the new password works.")
    else:
        print("❌ No admin access possible! Database may be corrupted.")

if __name__ == '__main__':
    main()