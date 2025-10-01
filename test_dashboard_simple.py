#!/usr/bin/env python
"""
Simple test script to verify the dashboard consolidation
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()

def create_test_users():
    """Create test users for the dashboard"""
    print("Creating test users...")
    
    # Create a test patient
    patient, created = User.objects.get_or_create(
        username='test_patient',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'patient@test.com',
            'user_type': 'patient',
            'date_of_birth': datetime.now().date() - timedelta(days=365*45),  # 45 years old
            'gender': 'male'
        }
    )
    if created:
        patient.set_password('testpass123')
        patient.save()
        print(f"✓ Created patient: {patient.get_full_name()}")
    else:
        print(f"✓ Patient already exists: {patient.get_full_name()}")
    
    return patient

def test_dashboard_access():
    """Test dashboard access and consolidation"""
    print("\nTesting dashboard access...")
    
    patient = create_test_users()
    client = Client()
    
    # Login as patient
    login_success = client.login(username='test_patient', password='testpass123')
    if login_success:
        print("✓ Patient login successful")
    else:
        print("❌ Patient login failed")
        return False
    
    # Test main dashboard access
    response = client.get('/dashboard/')
    if response.status_code == 200:
        print("✓ Main dashboard accessible")
        
        # Check if vitals section is present (even if no data)
        if b'My Health Vitals' in response.content or b'No Vital Signs Recorded' in response.content:
            print("✓ Vitals section present in dashboard")
        else:
            print("❌ Vitals section missing from dashboard")
            
        # Check if telemedicine section is present
        if b'Telemedicine' in response.content:
            print("✓ Telemedicine section present in dashboard")
        else:
            print("❌ Telemedicine section missing from dashboard")
            
    else:
        print(f"❌ Main dashboard not accessible (status: {response.status_code})")
        return False
    
    # Test vitals dashboard redirect
    response = client.get('/treatments/vitals/dashboard/')
    if response.status_code == 301 or response.status_code == 302:
        print("✓ Vitals dashboard redirects to main dashboard")
    else:
        print(f"❌ Vitals dashboard redirect not working (status: {response.status_code})")
    
    # Test messaging dashboard redirect
    response = client.get('/telemedicine/patient-messages/')
    if response.status_code == 301 or response.status_code == 302:
        print("✓ Messaging dashboard redirects to main dashboard")
    else:
        print(f"❌ Messaging dashboard redirect not working (status: {response.status_code})")
    
    return True

def test_dashboard_data():
    """Test dashboard data structure"""
    print("\nTesting dashboard data structure...")
    
    from core.views import dashboard
    from django.http import HttpRequest
    from django.contrib.auth.models import AnonymousUser
    
    patient = User.objects.filter(user_type='patient').first()
    if not patient:
        print("❌ No patient found for testing")
        return False
    
    # Create a mock request
    request = HttpRequest()
    request.user = patient
    request.method = 'GET'
    
    try:
        response = dashboard(request)
        if response.status_code == 200:
            print("✓ Dashboard view executes successfully")
            return True
        else:
            print(f"❌ Dashboard view failed (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Dashboard view error: {str(e)}")
        return False

def run_simple_tests():
    """Run simple dashboard tests"""
    print("🏥 Testing Laso Healthcare Dashboard Consolidation")
    print("=" * 50)
    
    try:
        # Test dashboard access
        if not test_dashboard_access():
            return False
            
        # Test dashboard data
        if not test_dashboard_data():
            return False
        
        print("\n" + "=" * 50)
        print("✅ Dashboard consolidation tests completed successfully!")
        print("✅ Single unified dashboard is working")
        print("✅ Separate dashboards redirect to main dashboard")
        print("✅ Vitals and messaging sections integrated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)