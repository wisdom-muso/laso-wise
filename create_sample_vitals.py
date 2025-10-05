#!/usr/bin/env python
"""
Create sample vitals data for testing the enhanced vitals dashboard
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
sys.path.append('/workspace/project/laso-wise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from treatments.models_vitals import VitalSign
from django.utils import timezone
from django.db import transaction

User = get_user_model()

def create_sample_vitals():
    """Create sample vitals data for testing"""
    print("🏥 Creating sample vitals data...")
    
    # Get or create a test patient
    patient, created = User.objects.get_or_create(
        username='testpatient',
        defaults={
            'email': 'patient@test.com',
            'first_name': 'Test',
            'last_name': 'Patient',
            'user_type': 'patient',
            'date_of_birth': datetime(1990, 1, 1).date(),
            'blood_type': 'O+',
        }
    )
    
    if created:
        patient.set_password('testpass123')
        patient.save()
        print(f"✅ Created test patient: {patient.username}")
    else:
        print(f"✅ Using existing patient: {patient.username}")
    
    # Create vitals for the last 30 days
    base_date = timezone.now() - timedelta(days=30)
    
    vitals_created = 0
    for i in range(30):
        # Create 1-2 vitals per day
        for j in range(random.randint(1, 2)):
            vital_date = base_date + timedelta(days=i, hours=random.randint(8, 20), minutes=random.randint(0, 59))
            
            # Generate realistic vital signs with some variation
            base_systolic = 120 + random.randint(-20, 30)
            base_diastolic = 80 + random.randint(-15, 20)
            base_hr = 72 + random.randint(-15, 25)
            
            # Ensure realistic ranges
            systolic_bp = max(90, min(180, base_systolic))
            diastolic_bp = max(60, min(110, base_diastolic))
            heart_rate = max(50, min(120, base_hr))
            
            # Determine risk level based on BP
            if systolic_bp >= 140 or diastolic_bp >= 90:
                risk_level = 'high'
            elif systolic_bp >= 130 or diastolic_bp >= 80:
                risk_level = 'elevated'
            else:
                risk_level = 'normal'
            
            try:
                vital = VitalSign(
                    patient=patient,
                    systolic_bp=systolic_bp,
                    diastolic_bp=diastolic_bp,
                    heart_rate=heart_rate,
                    temperature=Decimal(str(36.0 + random.uniform(0, 1.5))),
                    respiratory_rate=random.randint(12, 20),
                    oxygen_saturation=random.randint(95, 100),
                    weight=Decimal(str(70 + random.uniform(-10, 20))),
                    height=175,
                    cholesterol_total=random.randint(150, 250) if random.random() > 0.7 else None,
                    blood_glucose=random.randint(80, 140) if random.random() > 0.8 else None,
                    overall_risk_level=risk_level,
                    recorded_at=vital_date
                )
                # Save without triggering signals
                vital.save(update_fields=None)
            except Exception as e:
                print(f"⚠️ Error creating vital: {e}")
                continue
            vitals_created += 1
    
    print(f"✅ Created {vitals_created} vital sign records")
    
    # Create a recent high BP reading for testing alerts
    try:
        high_bp_vital = VitalSign(
            patient=patient,
            systolic_bp=155,
            diastolic_bp=95,
            heart_rate=88,
            temperature=Decimal('36.8'),
            respiratory_rate=16,
            oxygen_saturation=98,
            overall_risk_level='high',
            recorded_at=timezone.now() - timedelta(hours=2)
        )
        high_bp_vital.save(update_fields=None)
    except Exception as e:
        print(f"⚠️ Error creating high BP vital: {e}")
    
    print("✅ Created high BP reading for alert testing")
    
    # Get or create a doctor for recording vitals
    doctor, created = User.objects.get_or_create(
        username='testdoctor',
        defaults={
            'email': 'doctor@test.com',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'user_type': 'doctor',
        }
    )
    
    if created:
        doctor.set_password('testpass123')
        doctor.save()
        print(f"✅ Created test doctor: {doctor.username}")
    
    print("\n🎉 Sample vitals data created successfully!")
    print(f"📊 Total vitals records: {VitalSign.objects.filter(patient=patient).count()}")
    print(f"👤 Test patient: {patient.username} (password: testpass123)")
    print(f"👨‍⚕️ Test doctor: {doctor.username} (password: testpass123)")

if __name__ == '__main__':
    create_sample_vitals()