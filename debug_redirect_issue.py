#!/usr/bin/env python3
"""
Debug login redirect issues in LASO Healthcare System
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
from django.test import Client, RequestFactory
from django.urls import reverse, resolve
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from core.views_auth import CustomLoginView
from core.views import dashboard

User = get_user_model()

def test_url_resolution():
    """Test URL resolution for login and dashboard"""
    print("🔍 Testing URL Resolution...")
    
    try:
        # Test login URL
        login_url = reverse('login')
        print(f"✅ Login URL: {login_url}")
        
        # Test dashboard URL
        dashboard_url = reverse('dashboard')
        print(f"✅ Dashboard URL: {dashboard_url}")
        
        # Test URL resolution
        login_resolver = resolve('/login/')
        print(f"✅ Login resolver: {login_resolver.func} - {login_resolver.view_name}")
        
        dashboard_resolver = resolve('/dashboard/')
        print(f"✅ Dashboard resolver: {dashboard_resolver.func} - {dashboard_resolver.view_name}")
        
        return True
    except Exception as e:
        print(f"❌ URL resolution failed: {e}")
        return False

def test_user_authentication():
    """Test user authentication and user types"""
    print("\n🔐 Testing User Authentication...")
    
    try:
        # Test admin user
        admin_user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
        if admin_user:
            print(f"✅ Admin user authenticated: {admin_user.username}")
            print(f"   - Is staff: {admin_user.is_staff}")
            print(f"   - Is superuser: {admin_user.is_superuser}")
            print(f"   - User type: {admin_user.user_type}")
            print(f"   - is_patient(): {admin_user.is_patient()}")
            print(f"   - is_doctor(): {admin_user.is_doctor()}")
        else:
            print("❌ Admin user authentication failed")
        
        # Test patient user
        patient_user = authenticate(username='patient', password='testpatient123')
        if patient_user:
            print(f"✅ Patient user authenticated: {patient_user.username}")
            print(f"   - Is staff: {patient_user.is_staff}")
            print(f"   - Is superuser: {patient_user.is_superuser}")
            print(f"   - User type: {patient_user.user_type}")
            print(f"   - is_patient(): {patient_user.is_patient()}")
            print(f"   - is_doctor(): {patient_user.is_doctor()}")
        else:
            print("❌ Patient user authentication failed")
        
        return admin_user, patient_user
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        return None, None

def test_login_view_redirect_logic():
    """Test the CustomLoginView redirect logic"""
    print("\n🔄 Testing Login View Redirect Logic...")
    
    try:
        factory = RequestFactory()
        
        # Test admin user redirect
        admin_user = User.objects.get(username='admin')
        request = factory.post('/login/', {
            'username': 'admin',
            'password': '8gJW48Tz8YXDrF57'
        })
        
        # Add required middleware
        SessionMiddleware(lambda x: None).process_request(request)
        request.session.save()
        AuthenticationMiddleware(lambda x: None).process_request(request)
        MessageMiddleware(lambda x: None).process_request(request)
        
        # Set user
        request.user = admin_user
        
        # Test CustomLoginView get_success_url
        login_view = CustomLoginView()
        login_view.request = request
        login_view._user = admin_user
        
        success_url = login_view.get_success_url()
        print(f"✅ Admin user success URL: {success_url}")
        
        # Test patient user redirect
        patient_user = User.objects.get(username='patient')
        request.user = patient_user
        login_view._user = patient_user
        
        success_url = login_view.get_success_url()
        print(f"✅ Patient user success URL: {success_url}")
        
        return True
    except Exception as e:
        print(f"❌ Login view redirect test failed: {e}")
        return False

def test_dashboard_access():
    """Test dashboard access for different user types"""
    print("\n📊 Testing Dashboard Access...")
    
    try:
        client = Client()
        
        # Test admin dashboard access
        admin_login = client.login(username='admin', password='8gJW48Tz8YXDrF57')
        if admin_login:
            print("✅ Admin login successful")
            
            # Test dashboard access
            dashboard_response = client.get('/dashboard/')
            print(f"✅ Admin dashboard response: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("✅ Admin can access dashboard")
            elif dashboard_response.status_code == 302:
                print(f"⚠️  Admin dashboard redirects to: {dashboard_response.url}")
            else:
                print(f"❌ Admin dashboard access failed: {dashboard_response.status_code}")
        else:
            print("❌ Admin login failed")
        
        client.logout()
        
        # Test patient dashboard access
        patient_login = client.login(username='patient', password='testpatient123')
        if patient_login:
            print("✅ Patient login successful")
            
            # Test dashboard access
            dashboard_response = client.get('/dashboard/')
            print(f"✅ Patient dashboard response: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("✅ Patient can access dashboard")
            elif dashboard_response.status_code == 302:
                print(f"⚠️  Patient dashboard redirects to: {dashboard_response.url}")
            else:
                print(f"❌ Patient dashboard access failed: {dashboard_response.status_code}")
        else:
            print("❌ Patient login failed")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard access test failed: {e}")
        return False

def test_login_flow_simulation():
    """Simulate the complete login flow"""
    print("\n🔄 Simulating Complete Login Flow...")
    
    try:
        client = Client()
        
        # Test admin login flow
        print("Testing admin login flow...")
        
        # Get login page
        login_page = client.get('/login/')
        print(f"✅ Login page status: {login_page.status_code}")
        
        # Extract CSRF token
        csrf_token = None
        if hasattr(login_page, 'context') and login_page.context:
            csrf_token = login_page.context.get('csrf_token')
        
        if not csrf_token:
            # Try to extract from content
            content = login_page.content.decode('utf-8')
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        # Perform login
        login_data = {
            'username': 'admin',
            'password': '8gJW48Tz8YXDrF57',
        }
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        login_response = client.post('/login/', login_data, follow=False)
        print(f"✅ Admin login response: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print(f"✅ Admin login redirects to: {login_response.url}")
            
            # Follow the redirect
            final_response = client.get(login_response.url)
            print(f"✅ Final page status: {final_response.status_code}")
            
            if final_response.status_code == 200:
                print("✅ Admin successfully reached final page")
            else:
                print(f"❌ Admin final page failed: {final_response.status_code}")
        else:
            print(f"❌ Admin login failed: {login_response.status_code}")
        
        client.logout()
        
        # Test patient login flow
        print("\nTesting patient login flow...")
        
        # Get login page
        login_page = client.get('/login/')
        
        # Extract CSRF token
        csrf_token = None
        if hasattr(login_page, 'context') and login_page.context:
            csrf_token = login_page.context.get('csrf_token')
        
        if not csrf_token:
            # Try to extract from content
            content = login_page.content.decode('utf-8')
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        # Perform login
        login_data = {
            'username': 'patient',
            'password': 'testpatient123',
        }
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        login_response = client.post('/login/', login_data, follow=False)
        print(f"✅ Patient login response: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print(f"✅ Patient login redirects to: {login_response.url}")
            
            # Follow the redirect
            final_response = client.get(login_response.url)
            print(f"✅ Final page status: {final_response.status_code}")
            
            if final_response.status_code == 200:
                print("✅ Patient successfully reached final page")
            else:
                print(f"❌ Patient final page failed: {final_response.status_code}")
        else:
            print(f"❌ Patient login failed: {login_response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Login flow simulation failed: {e}")
        return False

def check_template_existence():
    """Check if required templates exist"""
    print("\n📄 Checking Template Existence...")
    
    templates_to_check = [
        'core/login.html',
        'core/patient_dashboard.html',
        'core/doctor_dashboard.html',
        'core/dashboard.html',
    ]
    
    import os
    from django.conf import settings
    
    for template in templates_to_check:
        template_found = False
        for template_dir in settings.TEMPLATES[0]['DIRS']:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print(f"✅ Template found: {template}")
                template_found = True
                break
        
        if not template_found:
            print(f"❌ Template missing: {template}")

def main():
    """Run all redirect debugging tests"""
    print("🔍 LASO Healthcare Login Redirect Debug")
    print("=" * 50)
    
    tests = [
        ("URL Resolution", test_url_resolution),
        ("User Authentication", test_user_authentication),
        ("Login View Redirect Logic", test_login_view_redirect_logic),
        ("Dashboard Access", test_dashboard_access),
        ("Login Flow Simulation", test_login_flow_simulation),
        ("Template Existence", check_template_existence),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 {test_name}...")
            result = test_func()
            results[test_name] = result if result is not None else True
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 REDIRECT DEBUG RESULTS")
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
    
    if failed == 0:
        print("\n🎉 All redirect tests passed!")
    else:
        print(f"\n⚠️  {failed} tests failed. Check the issues above.")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)