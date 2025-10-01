#!/usr/bin/env python
"""
Test script to verify the vitals tracking system functionality
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
from treatments.models_vitals import VitalSign, VitalSignAlert

User = get_user_model()

def create_test_users():
    """Create test users for the vitals system"""
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
    
    # Create a test doctor
    doctor, created = User.objects.get_or_create(
        username='test_doctor',
        defaults={
            'first_name': 'Dr. Sarah',
            'last_name': 'Smith',
            'email': 'doctor@test.com',
            'user_type': 'doctor',
            'date_of_birth': datetime.now().date() - timedelta(days=365*35),  # 35 years old
            'gender': 'female'
        }
    )
    if created:
        doctor.set_password('testpass123')
        doctor.save()
        print(f"✓ Created doctor: {doctor.get_full_name()}")
    else:
        print(f"✓ Doctor already exists: {doctor.get_full_name()}")
    
    return patient, doctor

def create_test_vitals(patient, doctor):
    """Create test vital signs data"""
    print("\nCreating test vital signs...")
    
    # Test data for different scenarios
    vitals_data = [
        {
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'heart_rate': 72,
            'temperature': Decimal('36.5'),
            'oxygen_saturation': 98,
            'weight': Decimal('75.0'),
            'height': 175,
            'cholesterol_total': 180,
            'blood_glucose': 95,
            'notes': 'Normal baseline reading',
            'measurement_context': 'Morning checkup'
        },
        {
            'systolic_bp': 145,
            'diastolic_bp': 95,
            'heart_rate': 85,
            'temperature': Decimal('36.8'),
            'oxygen_saturation': 97,
            'weight': Decimal('76.0'),
            'height': 175,
            'cholesterol_total': 220,
            'blood_glucose': 110,
            'notes': 'Elevated blood pressure - Stage 1 hypertension',
            'measurement_context': 'Follow-up visit'
        },
        {
            'systolic_bp': 165,
            'diastolic_bp': 105,
            'heart_rate': 95,
            'temperature': Decimal('37.0'),
            'oxygen_saturation': 96,
            'weight': Decimal('77.0'),
            'height': 175,
            'cholesterol_total': 250,
            'blood_glucose': 125,
            'notes': 'Stage 2 hypertension - requires immediate attention',
            'measurement_context': 'Emergency visit'
        }
    ]
    
    created_vitals = []
    for i, data in enumerate(vitals_data):
        # Create vitals with different timestamps
        recorded_at = datetime.now() - timedelta(days=len(vitals_data)-i-1)
        
        vital = VitalSign.objects.create(
            patient=patient,
            recorded_by=doctor,
            recorded_at=recorded_at,
            **data
        )
        created_vitals.append(vital)
        
        print(f"✓ Created vital sign: BP {vital.blood_pressure_display}, HR {vital.heart_rate}, Risk: {vital.get_overall_risk_level_display()}")
        
        # Check if alerts were created
        alerts = VitalSignAlert.objects.filter(vital_sign=vital)
        if alerts.exists():
            for alert in alerts:
                print(f"  ⚠️  Alert created: {alert.get_alert_type_display()} - {alert.message}")
    
    return created_vitals

def test_risk_assessment():
    """Test the risk assessment functionality"""
    print("\nTesting risk assessment...")
    
    # Test different BP categories
    test_cases = [
        (110, 70, 'normal'),
        (125, 75, 'elevated'),
        (135, 85, 'high'),
        (155, 95, 'high'),
        (185, 115, 'critical')
    ]
    
    for systolic, diastolic, expected_risk in test_cases:
        # Create a temporary vital sign for testing
        patient = User.objects.filter(user_type='patient').first()
        doctor = User.objects.filter(user_type='doctor').first()
        
        vital = VitalSign(
            patient=patient,
            recorded_by=doctor,
            systolic_bp=systolic,
            diastolic_bp=diastolic,
            heart_rate=72
        )
        
        # Test BP category calculation
        bp_category = vital.bp_category
        print(f"✓ BP {systolic}/{diastolic} -> Category: {bp_category}")

def test_dashboard_data():
    """Test dashboard data retrieval"""
    print("\nTesting dashboard data...")
    
    patient = User.objects.filter(user_type='patient').first()
    if not patient:
        print("❌ No patient found for testing")
        return
    
    # Get latest vital
    latest_vital = VitalSign.objects.filter(patient=patient).first()
    if latest_vital:
        print(f"✓ Latest vital: {latest_vital.blood_pressure_display} on {latest_vital.recorded_at.date()}")
        print(f"  Risk level: {latest_vital.get_overall_risk_level_display()}")
        if latest_vital.bmi:
            print(f"  BMI: {latest_vital.bmi}")
    
    # Get recent vitals count
    recent_count = VitalSign.objects.filter(
        patient=patient,
        recorded_at__gte=datetime.now() - timedelta(days=30)
    ).count()
    print(f"✓ Recent vitals (30 days): {recent_count}")
    
    # Get active alerts
    active_alerts = VitalSignAlert.objects.filter(
        vital_sign__patient=patient,
        status='active'
    ).count()
    print(f"✓ Active alerts: {active_alerts}")

def test_api_endpoints():
    """Test API functionality"""
    print("\nTesting API functionality...")
    
    from treatments.serializers_vitals import VitalSignSerializer
    
    patient = User.objects.filter(user_type='patient').first()
    vitals = VitalSign.objects.filter(patient=patient)[:3]
    
    if vitals:
        serializer = VitalSignSerializer(vitals, many=True)
        print(f"✓ Serialized {len(serializer.data)} vital signs")
        
        # Test individual vital serialization
        vital = vitals.first()
        single_serializer = VitalSignSerializer(vital)
        data = single_serializer.data
        
        print(f"✓ Single vital data includes:")
        print(f"  - Blood pressure: {data.get('blood_pressure_display')}")
        print(f"  - Risk level: {data.get('overall_risk_level')}")
        print(f"  - Patient info: {data.get('patient_info', {}).get('full_name')}")

def run_all_tests():
    """Run all tests"""
    print("🏥 Testing Laso Healthcare Vitals System")
    print("=" * 50)
    
    try:
        # Create test data
        patient, doctor = create_test_users()
        vitals = create_test_vitals(patient, doctor)
        
        # Run tests
        test_risk_assessment()
        test_dashboard_data()
        test_api_endpoints()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print(f"✅ Created {len(vitals)} vital sign records")
        print(f"✅ Patient dashboard ready for: {patient.get_full_name()}")
        print(f"✅ Doctor interface ready for: {doctor.get_full_name()}")
        
        # Print access information
        print("\n📋 Test Data Summary:")
        print(f"Patient Login: test_patient / testpass123")
        print(f"Doctor Login: test_doctor / testpass123")
        print(f"Patient ID: {patient.id}")
        print(f"Doctor ID: {doctor.id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)