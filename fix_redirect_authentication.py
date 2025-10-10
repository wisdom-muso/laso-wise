#!/usr/bin/env python3
"""
Fix redirect authentication issues in LASO Healthcare System
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

def fix_user_types():
    """Ensure users have correct user_type values"""
    print("🔧 Fixing user types...")
    try:
        # Fix admin user
        admin_user = User.objects.get(username='admin')
        if admin_user.user_type != 'admin':
            admin_user.user_type = 'admin'
            admin_user.save()
            print(f"✅ Fixed admin user type: {admin_user.user_type}")
        else:
            print(f"✅ Admin user type already correct: {admin_user.user_type}")
        
        # Fix patient user
        try:
            patient_user = User.objects.get(username='patient')
            if patient_user.user_type != 'patient':
                patient_user.user_type = 'patient'
                patient_user.save()
                print(f"✅ Fixed patient user type: {patient_user.user_type}")
            else:
                print(f"✅ Patient user type already correct: {patient_user.user_type}")
        except User.DoesNotExist:
            print("⚠️  Patient user doesn't exist, will create it")
            patient_user = User.objects.create_user(
                username='patient',
                email='patient@test.com',
                password='testpatient123',
                first_name='Test',
                last_name='Patient',
                user_type='patient'
            )
            print(f"✅ Created patient user with type: {patient_user.user_type}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to fix user types: {e}")
        return False

def clear_problematic_sessions():
    """Clear any problematic sessions"""
    print("🧹 Clearing problematic sessions...")
    try:
        session_count = Session.objects.count()
        Session.objects.all().delete()
        print(f"✅ Cleared {session_count} sessions")
        return True
    except Exception as e:
        print(f"❌ Failed to clear sessions: {e}")
        return False

def test_dashboard_view():
    """Test if dashboard view works correctly"""
    print("📊 Testing dashboard view...")
    try:
        from django.test import Client
        
        client = Client()
        
        # Test patient login and dashboard access
        login_success = client.login(username='patient', password='testpatient123')
        if login_success:
            print("✅ Patient login successful")
            
            # Test dashboard access
            response = client.get('/dashboard/')
            print(f"✅ Dashboard response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Dashboard loads successfully")
                return True
            elif response.status_code == 302:
                print(f"⚠️  Dashboard redirects to: {response.url}")
                return False
            else:
                print(f"❌ Dashboard failed with status: {response.status_code}")
                return False
        else:
            print("❌ Patient login failed")
            return False
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def create_simple_dashboard_template():
    """Create a simple dashboard template if it doesn't exist"""
    print("📄 Ensuring dashboard template exists...")
    try:
        import os
        from django.conf import settings
        
        # Find templates directory
        template_dirs = settings.TEMPLATES[0]['DIRS']
        if not template_dirs:
            print("❌ No template directories configured")
            return False
        
        template_dir = template_dirs[0]
        core_template_dir = os.path.join(template_dir, 'core')
        
        # Ensure core template directory exists
        os.makedirs(core_template_dir, exist_ok=True)
        
        # Check if patient_dashboard.html exists
        patient_dashboard_path = os.path.join(core_template_dir, 'patient_dashboard.html')
        
        if not os.path.exists(patient_dashboard_path):
            print("⚠️  Creating simple patient dashboard template...")
            
            simple_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Dashboard - LASO Healthcare</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #007bff; color: white; padding: 20px; border-radius: 5px; }
        .content { margin-top: 20px; }
        .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome, {{ user.get_full_name|default:user.username }}!</h1>
        <p>Patient Dashboard</p>
    </div>
    
    <div class="content">
        <div class="card">
            <h3>Dashboard Information</h3>
            <p>Welcome to your patient dashboard. This is a simplified version to test login functionality.</p>
            <p>User Type: {{ user.user_type }}</p>
            <p>Email: {{ user.email }}</p>
        </div>
        
        <div class="card">
            <h3>Quick Actions</h3>
            <ul>
                <li><a href="/appointments/">View Appointments</a></li>
                <li><a href="/treatments/">View Treatments</a></li>
                <li><a href="/logout/">Logout</a></li>
            </ul>
        </div>
    </div>
</body>
</html>'''
            
            with open(patient_dashboard_path, 'w') as f:
                f.write(simple_template)
            
            print(f"✅ Created simple patient dashboard template at: {patient_dashboard_path}")
        else:
            print("✅ Patient dashboard template already exists")
        
        # Check if doctor_dashboard.html exists
        doctor_dashboard_path = os.path.join(core_template_dir, 'doctor_dashboard.html')
        
        if not os.path.exists(doctor_dashboard_path):
            print("⚠️  Creating simple doctor dashboard template...")
            
            simple_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doctor Dashboard - LASO Healthcare</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #28a745; color: white; padding: 20px; border-radius: 5px; }
        .content { margin-top: 20px; }
        .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome, Dr. {{ user.get_full_name|default:user.username }}!</h1>
        <p>Doctor Dashboard</p>
    </div>
    
    <div class="content">
        <div class="card">
            <h3>Dashboard Information</h3>
            <p>Welcome to your doctor dashboard. This is a simplified version to test login functionality.</p>
            <p>User Type: {{ user.user_type }}</p>
            <p>Specialization: {{ user.specialization|default:"Not specified" }}</p>
        </div>
        
        <div class="card">
            <h3>Quick Actions</h3>
            <ul>
                <li><a href="/appointments/">Manage Appointments</a></li>
                <li><a href="/treatments/">View Treatments</a></li>
                <li><a href="/core/patients/">View Patients</a></li>
                <li><a href="/logout/">Logout</a></li>
            </ul>
        </div>
    </div>
</body>
</html>'''
            
            with open(doctor_dashboard_path, 'w') as f:
                f.write(simple_template)
            
            print(f"✅ Created simple doctor dashboard template at: {doctor_dashboard_path}")
        else:
            print("✅ Doctor dashboard template already exists")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create dashboard templates: {e}")
        return False

def test_complete_login_flow():
    """Test the complete login flow"""
    print("🔄 Testing complete login flow...")
    try:
        from django.test import Client
        
        client = Client()
        
        # Test patient login flow
        print("Testing patient login flow...")
        
        # Get login page
        login_page = client.get('/login/')
        if login_page.status_code != 200:
            print(f"❌ Login page failed: {login_page.status_code}")
            return False
        
        print("✅ Login page accessible")
        
        # Perform login
        login_response = client.post('/login/', {
            'username': 'patient',
            'password': 'testpatient123'
        }, follow=False)
        
        print(f"✅ Login response status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_url = login_response.url
            print(f"✅ Login redirects to: {redirect_url}")
            
            # Follow the redirect
            final_response = client.get(redirect_url)
            print(f"✅ Final page status: {final_response.status_code}")
            
            if final_response.status_code == 200:
                print("✅ Patient successfully reached dashboard!")
                return True
            else:
                print(f"❌ Final page failed: {final_response.status_code}")
                return False
        else:
            print(f"❌ Login didn't redirect: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Complete login flow test failed: {e}")
        return False

def main():
    """Run all redirect fixes"""
    print("🔧 LASO Healthcare Redirect Authentication Fix")
    print("=" * 50)
    
    steps = [
        ("Fix User Types", fix_user_types),
        ("Clear Problematic Sessions", clear_problematic_sessions),
        ("Create Dashboard Templates", create_simple_dashboard_template),
        ("Test Dashboard View", test_dashboard_view),
        ("Test Complete Login Flow", test_complete_login_flow),
    ]
    
    results = {}
    for step_name, step_func in steps:
        try:
            print(f"\n🔧 {step_name}...")
            result = step_func()
            results[step_name] = result
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            results[step_name] = False
    
    print("\n" + "=" * 50)
    print("📊 REDIRECT FIX RESULTS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for step_name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{step_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} successful, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All redirect fixes applied successfully!")
        print("\n🔑 TEST THE LOGIN NOW:")
        print("1. Go to http://65.108.91.110/login/")
        print("2. Login with: patient / testpatient123")
        print("3. You should be redirected to the dashboard")
    else:
        print(f"\n⚠️  {failed} fixes failed. Check the issues above.")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)