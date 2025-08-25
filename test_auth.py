#!/usr/bin/env python3
"""
Quick authentication test script
"""
import requests
import json

# Test credentials
test_users = [
    {"username": "admin", "password": "admin123"},
    {"username": "arazumut", "password": "test123"},  # Try common passwords
    {"username": "arazumut", "password": "password"},
    {"username": "arazumut", "password": "123456"},
    {"username": "araz", "password": "test123"},
    {"username": "araz", "password": "password"},
]

base_url = "http://65.108.91.110:8000"

print("🧪 Testing authentication with debug endpoint...")
print()

for user in test_users:
    try:
        response = requests.post(
            f"{base_url}/debug/auth/",
            json=user,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User: {user['username']}")
            print(f"   User exists: {data.get('user_exists', False)}")
            print(f"   Auth success: {data.get('auth_success', False)}")
            if data.get('user_info'):
                print(f"   User info: {data['user_info']}")
            print()
        else:
            print(f"❌ Error testing {user['username']}: {response.status_code}")
            print(f"   Response: {response.text}")
            print()
            
    except Exception as e:
        print(f"❌ Exception testing {user['username']}: {e}")
        print()

print("🎯 Try these credentials in the browser:")
print("   http://65.108.91.110:8000/login/")
print()
print("📋 Common issues to check:")
print("   1. Password might be different than expected")
print("   2. Username might be case-sensitive")
print("   3. Authentication backend issues")
print("   4. Session/CSRF token issues")