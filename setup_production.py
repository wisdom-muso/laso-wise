#!/usr/bin/env python
"""
LASO Digital Health System - Production Setup Script
This script sets up the system for production use with sample data.
"""
import os
import django
import sys
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from vitals.models import VitalCategory
from telemedicine.models import VideoProviderConfig
from core.models import HospitalSettings
from accounts.models import Profile

User = get_user_model()

def setup_production():
    """Setup the system for production"""
    print("🏥 Setting up LASO Digital Health System for Production...")
    
    # 1. Run migrations
    print("📋 Running database migrations...")
    call_command('migrate', verbosity=1)
    
    # 2. Load default vital categories
    print("💊 Loading default vital categories...")
    try:
        call_command('loaddata', 'vitals/fixtures/default_vital_categories.json')
        print("✅ Vital categories loaded successfully")
    except Exception as e:
        print(f"⚠️  Could not load vital categories: {e}")
    
    # 3. Create superuser if not exists
    print("👨‍💼 Setting up admin user...")
    try:
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@laso-health.com',
                password='admin123!',
                first_name='System',
                last_name='Administrator'
            )
            print("✅ Superuser created: admin / admin123!")
        else:
            print("ℹ️  Superuser already exists")
    except Exception as e:
        print(f"⚠️  Could not create superuser: {e}")
    
    # 4. Setup default hospital settings
    print("🏨 Configuring hospital settings...")
    try:
        hospital_settings, created = HospitalSettings.objects.get_or_create(
            defaults={
                'hospital_name': 'LASO Digital Health Center',
                'address': '123 Healthcare Boulevard',
                'city': 'Medical City',
                'state': 'CA',
                'postal_code': '90210',
                'country': 'USA',
                'phone': '+1 (555) 123-4567',
                'email': 'info@laso-health.com',
                'website': 'https://laso-health.com',
                'timezone': 'America/Los_Angeles',
                'currency': 'USD',
                'email_notifications': True,
                'appointment_reminders': True,
                'reminder_hours_before': 24,
                'max_appointments_per_day': 50,
                'appointment_duration': 30,
                'allow_online_booking': True,
            }
        )
        if created:
            print("✅ Hospital settings configured")
        else:
            print("ℹ️  Hospital settings already exist")
    except Exception as e:
        print(f"⚠️  Could not setup hospital settings: {e}")
    
    # 5. Setup default video provider configs
    print("🎥 Configuring telemedicine providers...")
    try:
        # Zoom configuration
        zoom_config, created = VideoProviderConfig.objects.get_or_create(
            provider='zoom',
            defaults={
                'is_active': False,  # Requires API keys to activate
                'max_participants': 50,
                'recording_enabled': True,
                'settings_json': {
                    'waiting_room': True,
                    'join_before_host': False,
                    'mute_upon_entry': True,
                }
            }
        )
        
        # Google Meet configuration
        meet_config, created = VideoProviderConfig.objects.get_or_create(
            provider='google_meet',
            defaults={
                'is_active': False,  # Requires API keys to activate
                'max_participants': 25,
                'recording_enabled': False,
                'settings_json': {
                    'auto_admit': False,
                    'quick_access': True,
                }
            }
        )
        print("✅ Video provider configurations ready")
    except Exception as e:
        print(f"⚠️  Could not setup video providers: {e}")
    
    # 6. Create sample doctor if needed
    print("👨‍⚕️ Setting up sample doctor...")
    try:
        if not User.objects.filter(role='doctor').exists():
            doctor = User.objects.create_user(
                username='dr.smith',
                email='dr.smith@laso-health.com',
                password='doctor123!',
                first_name='John',
                last_name='Smith',
                role='doctor'
            )
            
            # Create doctor profile
            if hasattr(doctor, 'profile'):
                doctor.profile.specialization = 'General Medicine'
                doctor.profile.experience = 10
                doctor.profile.price_per_consultation = 150.00
                doctor.profile.phone = '+1 (555) 987-6543'
                doctor.profile.save()
            
            print("✅ Sample doctor created: dr.smith / doctor123!")
        else:
            print("ℹ️  Doctors already exist")
    except Exception as e:
        print(f"⚠️  Could not create sample doctor: {e}")
    
    # 7. Create sample patient if needed
    print("👤 Setting up sample patient...")
    try:
        if not User.objects.filter(role='patient').exists():
            patient = User.objects.create_user(
                username='patient1',
                email='patient@example.com',
                password='patient123!',
                first_name='Jane',
                last_name='Doe',
                role='patient'
            )
            
            # Create patient profile
            if hasattr(patient, 'profile'):
                patient.profile.age = 35
                patient.profile.gender = 'Female'
                patient.profile.phone = '+1 (555) 555-0123'
                patient.profile.city = 'Medical City'
                patient.profile.save()
            
            print("✅ Sample patient created: patient1 / patient123!")
        else:
            print("ℹ️  Patients already exist")
    except Exception as e:
        print(f"⚠️  Could not create sample patient: {e}")
    
    # 8. Collect static files
    print("📁 Collecting static files...")
    try:
        call_command('collectstatic', '--noinput', verbosity=1)
        print("✅ Static files collected")
    except Exception as e:
        print(f"⚠️  Could not collect static files: {e}")
    
    print("\n🎉 LASO Digital Health System is ready for production!")
    print("\n📝 Default Credentials:")
    print("   Admin: admin / admin123!")
    print("   Doctor: dr.smith / doctor123!")
    print("   Patient: patient1 / patient123!")
    print("\n🌐 Access Points:")
    print("   Main Site: http://localhost:8005/")
    print("   Admin Dashboard: http://localhost:8005/admin/")
    print("   Enhanced Dashboard: http://localhost:8005/admin/enhanced-dashboard/")
    print("   API Health: http://localhost:8005/api/health/")
    print("\n⚙️  Features Ready:")
    print("   ✅ EHR & SOAP Notes")
    print("   ✅ Vitals Monitoring & Analytics")
    print("   ✅ Telemedicine (Configure API Keys)")
    print("   ✅ Appointment Booking")
    print("   ✅ User Management")
    print("   ✅ Admin Analytics Dashboard")

if __name__ == '__main__':
    setup_production()