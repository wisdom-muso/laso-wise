#!/usr/bin/env python3
"""
Test login functionality after applying fixes
"""
import requests
import sys
from urllib.parse import urljoin

BASE_URL = "http://65.108.91.110"

def test_login_page():
    """Test if login page loads correctly"""
    print("🌐 Testing login page accessibility...")
    try:
        response = requests.get(urljoin(BASE_URL, "/login/"), timeout=10)
        if response.status_code == 200:
            print("✅ Login page loads successfully")
            return True
        else:
            print(f"❌ Login page returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to access login page: {e}")
        return False

def test_admin_login_page():
    """Test if admin login page loads correctly"""
    print("🌐 Testing admin login page accessibility...")
    try:
        response = requests.get(urljoin(BASE_URL, "/admin/login/"), timeout=10)
        if response.status_code == 200:
            print("✅ Admin login page loads successfully")
            return True
        else:
            print(f"❌ Admin login page returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to access admin login page: {e}")
        return False

def test_patient_login():
    """Test patient login functionality"""
    print("🔐 Testing patient login...")
    try:
        session = requests.Session()
        
        # Get login page to retrieve CSRF token
        login_page = session.get(urljoin(BASE_URL, "/login/"), timeout=10)
        if login_page.status_code != 200:
            print(f"❌ Could not access login page: {login_page.status_code}")
            return False
        
        # Extract CSRF token
        csrf_token = None
        for line in login_page.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                csrf_token = line.split('value="')[1].split('"')[0]
                break
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return False
        
        # Attempt login
        login_data = {
            'username': 'patient',
            'password': 'testpatient123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(
            urljoin(BASE_URL, "/login/"),
            data=login_data,
            timeout=10,
            allow_redirects=False
        )
        
        # Check if login was successful (should redirect)
        if response.status_code in [302, 301]:
            print("✅ Patient login successful (redirected)")
            return True
        elif response.status_code == 200:
            # Check if we're still on login page (login failed)
            if "/login/" in response.url or "login" in response.text.lower():
                print("❌ Patient login failed - stayed on login page")
                return False
            else:
                print("✅ Patient login successful")
                return True
        else:
            print(f"❌ Patient login returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Patient login test failed: {e}")
        return False

def test_admin_login():
    """Test admin login functionality"""
    print("🔐 Testing admin login...")
    try:
        session = requests.Session()
        
        # Get admin login page to retrieve CSRF token
        login_page = session.get(urljoin(BASE_URL, "/admin/login/"), timeout=10)
        if login_page.status_code != 200:
            print(f"❌ Could not access admin login page: {login_page.status_code}")
            return False
        
        # Extract CSRF token
        csrf_token = None
        for line in login_page.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                csrf_token = line.split('value="')[1].split('"')[0]
                break
        
        if not csrf_token:
            print("❌ Could not find CSRF token in admin login")
            return False
        
        # Attempt admin login
        login_data = {
            'username': 'admin',
            'password': '8gJW48Tz8YXDrF57',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/admin/'
        }
        
        response = session.post(
            urljoin(BASE_URL, "/admin/login/"),
            data=login_data,
            timeout=10,
            allow_redirects=False
        )
        
        # Check if login was successful (should redirect)
        if response.status_code in [302, 301]:
            print("✅ Admin login successful (redirected)")
            return True
        elif response.status_code == 200:
            # Check if we're still on login page (login failed)
            if "/admin/login/" in response.url or "login" in response.text.lower():
                print("❌ Admin login failed - stayed on login page")
                return False
            else:
                print("✅ Admin login successful")
                return True
        else:
            print(f"❌ Admin login returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Admin login test failed: {e}")
        return False

def main():
    """Run all login tests"""
    print("🧪 LASO Healthcare Login Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Login Page Access", test_login_page),
        ("Admin Login Page Access", test_admin_login_page),
        ("Patient Login", test_patient_login),
        ("Admin Login", test_admin_login),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 {test_name}...")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
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
        print("\n🎉 All login tests passed! The authentication system is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the application logs.")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)