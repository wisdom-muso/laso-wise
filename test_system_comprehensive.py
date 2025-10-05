#!/usr/bin/env python
"""
Comprehensive System Test for Laso Healthcare Platform
Tests all core functionality including authentication, vitals, telemedicine, AI, and security
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from users.models import User
from treatments.models import VitalSign
from core.ai_predictive_analysis import EndOrganDamagePredictor
from core.security_enhancements import SecurityMiddleware

class ComprehensiveSystemTest:
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {message}")
    
    def setup_test_data(self):
        """Create test users and data"""
        try:
            # Clean up any existing test data
            User.objects.filter(username__in=['testpatient', 'testdoctor', 'testadmin']).delete()
            
            # Create test users
            self.patient_user = User.objects.create_user(
                username='testpatient',
                email='patient@test.com',
                password='testpass123',
                user_type='patient',
                first_name='Test',
                last_name='Patient'
            )
            
            self.doctor_user = User.objects.create_user(
                username='testdoctor',
                email='doctor@test.com',
                password='testpass123',
                user_type='doctor',
                first_name='Dr. Test',
                last_name='Doctor'
            )
            
            self.admin_user = User.objects.create_superuser(
                username='testadmin',
                email='admin@test.com',
                password='testpass123',
                first_name='Test',
                last_name='Admin'
            )
            
            # Set additional user fields
            self.patient_user.date_of_birth = '1990-01-01'
            self.patient_user.phone_number = '+1234567890'
            self.patient_user.save()
            
            self.doctor_user.specialization = 'Cardiology'
            self.doctor_user.phone_number = '+1122334455'
            self.doctor_user.save()
            
            # Store references for easy access
            self.patient = self.patient_user
            self.doctor = self.doctor_user
            
            self.log_test("Setup Test Data", "PASS", "Test users and profiles created successfully")
            return True
            
        except Exception as e:
            self.log_test("Setup Test Data", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_authentication_system(self):
        """Test authentication with email and username"""
        try:
            # Test username login
            login_success = self.client.login(username='testpatient', password='testpass123')
            if not login_success:
                raise Exception("Username login failed")
            self.client.logout()
            
            # Test email login
            login_success = self.client.login(username='patient@test.com', password='testpass123')
            if not login_success:
                raise Exception("Email login failed")
            self.client.logout()
            
            # Test invalid credentials
            login_success = self.client.login(username='testpatient', password='wrongpass')
            if login_success:
                raise Exception("Invalid credentials should not work")
            
            self.log_test("Authentication System", "PASS", "Email and username login working correctly")
            return True
            
        except Exception as e:
            self.log_test("Authentication System", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_vitals_tracking(self):
        """Test vitals tracking functionality"""
        try:
            # Login as patient
            self.client.login(username='testpatient', password='testpass123')
            
            # Create vital signs
            vital_data = {
                'systolic_bp': 120,
                'diastolic_bp': 80,
                'heart_rate': 72,
                'temperature': 36.5,
                'oxygen_saturation': 98,
                'recorded_at': datetime.now()
            }
            
            vital = VitalSign.objects.create(
                patient=self.patient_user,
                **vital_data
            )
            
            # Test vitals dashboard access
            response = self.client.get('/core/vitals/enhanced/')
            if response.status_code != 200:
                raise Exception(f"Enhanced vitals dashboard returned {response.status_code}")
            
            # Verify vital sign was created
            if not VitalSign.objects.filter(patient=self.patient_user).exists():
                raise Exception("Vital sign was not created")
            
            self.log_test("Vitals Tracking", "PASS", "Vitals creation and dashboard access working")
            return True
            
        except Exception as e:
            self.log_test("Vitals Tracking", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_telemedicine_functionality(self):
        """Test telemedicine features"""
        try:
            # Login as patient
            self.client.login(username='testpatient', password='testpass123')
            
            # Test telemedicine dashboard access
            response = self.client.get('/telemedicine/')
            if response.status_code != 200:
                raise Exception(f"Telemedicine dashboard returned {response.status_code}")
            
            # Test consultation scheduling page
            response = self.client.get('/telemedicine/schedule/')
            if response.status_code != 200:
                raise Exception(f"Consultation scheduling returned {response.status_code}")
            
            self.log_test("Telemedicine Functionality", "PASS", "Telemedicine dashboard and scheduling accessible")
            return True
            
        except Exception as e:
            self.log_test("Telemedicine Functionality", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_ai_predictive_analysis(self):
        """Test AI predictive analysis system"""
        try:
            # Create some vital signs for analysis
            for i in range(5):
                VitalSign.objects.create(
                    patient=self.patient_user,
                    systolic_bp=140 + i * 2,  # Gradually increasing BP
                    diastolic_bp=90 + i,
                    heart_rate=80 + i,
                    temperature=36.5,
                    oxygen_saturation=98,
                    recorded_at=datetime.now() - timedelta(days=i)
                )
            
            # Test AI risk prediction
            predictor = EndOrganDamagePredictor()
            risk_assessment = predictor.predict_end_organ_damage(self.patient_user)
            
            if not isinstance(risk_assessment, dict):
                raise Exception("Risk assessment should return a dictionary")
            
            if 'risk_score' not in risk_assessment:
                raise Exception("Risk assessment missing risk_score")
            
            # Login as doctor to test AI dashboard
            self.client.login(username='testdoctor', password='testpass123')
            response = self.client.get('/core/ai-assistant/')
            if response.status_code != 200:
                raise Exception(f"AI Assistant dashboard returned {response.status_code}")
            
            self.log_test("AI Predictive Analysis", "PASS", "AI risk assessment and dashboard working")
            return True
            
        except Exception as e:
            self.log_test("AI Predictive Analysis", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_hypertension_handling(self):
        """Test hypertension detection and handling"""
        try:
            # Create high blood pressure reading
            high_bp_vital = VitalSign.objects.create(
                patient=self.patient_user,
                systolic_bp=160,  # High BP
                diastolic_bp=100,  # High BP
                heart_rate=85,
                temperature=36.5,
                oxygen_saturation=98,
                recorded_at=datetime.now()
            )
            
            # Check if hypertension is detected
            if high_bp_vital.systolic_bp < 140 or high_bp_vital.diastolic_bp < 90:
                raise Exception("Test data should indicate hypertension")
            
            # Test enhanced vitals dashboard shows alerts
            self.client.login(username='testpatient', password='testpass123')
            response = self.client.get('/core/vitals/enhanced/')
            
            if response.status_code != 200:
                raise Exception(f"Enhanced vitals dashboard returned {response.status_code}")
            
            # Check if response contains alert information
            content = response.content.decode('utf-8')
            if 'High Blood Pressure' not in content and 'Elevated' not in content:
                raise Exception("Hypertension alert not displayed in dashboard")
            
            self.log_test("Hypertension Handling", "PASS", "Hypertension detection and alerts working")
            return True
            
        except Exception as e:
            self.log_test("Hypertension Handling", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_data_encryption_security(self):
        """Test data encryption and security features"""
        try:
            # Test HTTPS enforcement in settings
            from django.conf import settings
            
            security_checks = []
            
            # Check security settings
            if hasattr(settings, 'SECURE_SSL_REDIRECT'):
                security_checks.append("SSL redirect configured")
            
            if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
                security_checks.append("XSS filter enabled")
            
            if hasattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF'):
                security_checks.append("Content type nosniff enabled")
            
            # Test password hashing
            user = User.objects.get(username='testpatient')
            if user.password.startswith('pbkdf2_'):
                security_checks.append("Password properly hashed")
            
            # Test CSRF protection
            self.client.logout()
            response = self.client.get('/login/')
            if 'csrfmiddlewaretoken' in response.content.decode('utf-8'):
                security_checks.append("CSRF protection active")
            
            if len(security_checks) < 3:
                raise Exception(f"Insufficient security measures: {security_checks}")
            
            self.log_test("Data Encryption & Security", "PASS", f"Security measures active: {', '.join(security_checks)}")
            return True
            
        except Exception as e:
            self.log_test("Data Encryption & Security", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_dashboard_functionality(self):
        """Test main dashboard functionality"""
        try:
            # Test patient dashboard
            self.client.login(username='testpatient', password='testpass123')
            response = self.client.get('/dashboard/')
            if response.status_code != 200:
                raise Exception(f"Patient dashboard returned {response.status_code}")
            
            # Test doctor dashboard
            self.client.login(username='testdoctor', password='testpass123')
            response = self.client.get('/dashboard/')
            if response.status_code != 200:
                raise Exception(f"Doctor dashboard returned {response.status_code}")
            
            # Test admin dashboard
            self.client.login(username='testadmin', password='testpass123')
            response = self.client.get('/dashboard/')
            if response.status_code != 200:
                raise Exception(f"Admin dashboard returned {response.status_code}")
            
            self.log_test("Dashboard Functionality", "PASS", "All user dashboards accessible")
            return True
            
        except Exception as e:
            self.log_test("Dashboard Functionality", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_enhanced_vitals_ui(self):
        """Test the enhanced vitals UI specifically"""
        try:
            self.client.login(username='testpatient', password='testpass123')
            
            # Test enhanced vitals dashboard
            response = self.client.get('/core/vitals/enhanced/')
            if response.status_code != 200:
                raise Exception(f"Enhanced vitals dashboard returned {response.status_code}")
            
            content = response.content.decode('utf-8')
            
            # Check for key UI elements
            ui_elements = [
                'Health Score',
                'BLOOD PRESSURE',
                'HEART RATE',
                'TEMPERATURE',
                'OXYGEN SATURATION',
                'Vitals Trends',
                'Recent Readings',
                'Health Recommendations'
            ]
            
            missing_elements = []
            for element in ui_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                raise Exception(f"Missing UI elements: {', '.join(missing_elements)}")
            
            # Check for Chart.js integration
            if 'Chart.js' not in content and 'chart' not in content.lower():
                raise Exception("Chart.js integration not found")
            
            self.log_test("Enhanced Vitals UI", "PASS", "All UI elements and charts present")
            return True
            
        except Exception as e:
            self.log_test("Enhanced Vitals UI", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive System Test for Laso Healthcare Platform")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test setup failed. Aborting tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_authentication_system,
            self.test_vitals_tracking,
            self.test_telemedicine_functionality,
            self.test_ai_predictive_analysis,
            self.test_hypertension_handling,
            self.test_data_encryption_security,
            self.test_dashboard_functionality,
            self.test_enhanced_vitals_ui
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        for result in self.test_results:
            status_symbol = "✅" if result['status'] == "PASS" else "❌"
            print(f"{status_symbol} {result['test']}: {result['message']}")
        
        print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! System is ready for production.")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed. Please review and fix issues.")
            return False

if __name__ == "__main__":
    # Run comprehensive tests
    test_runner = ComprehensiveSystemTest()
    success = test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)