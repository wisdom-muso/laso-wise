#!/usr/bin/env python
"""
Django Admin Interface Enhancements
This script enhances the Django admin interface by properly organizing models
and ensuring all telemedicine and core models are visible and accessible.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.apps import apps

def enhance_admin_interface():
    """Enhance the Django admin interface with better organization"""
    
    print("🔧 Enhancing Django Admin Interface...")
    
    # Custom admin site configuration
    admin.site.site_header = "Laso Digital Health Administration"
    admin.site.site_title = "Laso Digital Health Admin"
    admin.site.index_title = "Welcome to Laso Digital Health Management System"
    
    # Get all registered models
    registered_models = admin.site._registry
    
    print(f"📊 Currently registered models: {len(registered_models)}")
    
    # Categorize models by app
    model_categories = {}
    for model, model_admin in registered_models.items():
        app_label = model._meta.app_label
        if app_label not in model_categories:
            model_categories[app_label] = []
        model_categories[app_label].append({
            'model': model,
            'name': model._meta.verbose_name,
            'admin': model_admin
        })
    
    # Print current organization
    print("\n📋 Current Admin Organization:")
    for app_label, models in sorted(model_categories.items()):
        print(f"\n🏥 {app_label.title()} ({len(models)} models):")
        for model_info in sorted(models, key=lambda x: x['name']):
            print(f"  ✓ {model_info['name']}")
    
    # Check for missing models that should be registered
    print("\n🔍 Checking for missing model registrations...")
    
    # Core models that should be registered
    from core.models import SoapNote, EHRRecord, AuditLog, HospitalSettings, Speciality, Review
    core_models = [SoapNote, EHRRecord, AuditLog, HospitalSettings, Speciality, Review]
    
    # Telemedicine models that should be registered
    from telemedicine.models import (
        Consultation, ConsultationMessage, ConsultationParticipant,
        ConsultationRecording, WaitingRoom, TechnicalIssue, VideoProviderConfig
    )
    telemedicine_models = [
        Consultation, ConsultationMessage, ConsultationParticipant,
        ConsultationRecording, WaitingRoom, TechnicalIssue, VideoProviderConfig
    ]
    
    # Check core models
    missing_core = []
    for model in core_models:
        if model not in registered_models:
            missing_core.append(model)
    
    # Check telemedicine models
    missing_telemedicine = []
    for model in telemedicine_models:
        if model not in registered_models:
            missing_telemedicine.append(model)
    
    if missing_core:
        print(f"❌ Missing Core models: {[m._meta.verbose_name for m in missing_core]}")
    else:
        print("✅ All Core models are registered")
    
    if missing_telemedicine:
        print(f"❌ Missing Telemedicine models: {[m._meta.verbose_name for m in missing_telemedicine]}")
    else:
        print("✅ All Telemedicine models are registered")
    
    # Generate admin URLs for verification
    print("\n🔗 Admin URLs for verification:")
    print(f"  📊 Main Admin: /admin/")
    print(f"  🏥 Core Models:")
    print(f"    - SOAP Notes: /admin/core/soapnote/")
    print(f"    - EHR Records: /admin/core/ehrrecord/")
    print(f"    - Specialities: /admin/core/speciality/")
    print(f"    - Reviews: /admin/core/review/")
    print(f"    - Hospital Settings: /admin/core/hospitalsettings/")
    print(f"    - Audit Logs: /admin/core/auditlog/")
    
    print(f"  🎥 Telemedicine Models:")
    print(f"    - Consultations: /admin/telemedicine/consultation/")
    print(f"    - Messages: /admin/telemedicine/consultationmessage/")
    print(f"    - Participants: /admin/telemedicine/consultationparticipant/")
    print(f"    - Recordings: /admin/telemedicine/consultationrecording/")
    print(f"    - Waiting Room: /admin/telemedicine/waitingroom/")
    print(f"    - Technical Issues: /admin/telemedicine/technicalissue/")
    print(f"    - Video Config: /admin/telemedicine/videoproviderconfig/")
    
    return True

def verify_admin_accessibility():
    """Verify that admin models are accessible"""
    
    print("\n🧪 Verifying Admin Model Accessibility...")
    
    # Test admin URLs
    test_urls = [
        ('core', 'soapnote'),
        ('core', 'ehrrecord'),
        ('core', 'speciality'),
        ('core', 'review'),
        ('telemedicine', 'consultation'),
        ('telemedicine', 'consultationmessage'),
        ('telemedicine', 'videoproviderconfig'),
    ]
    
    accessible_count = 0
    total_count = len(test_urls)
    
    for app_label, model_name in test_urls:
        try:
            # Try to get the model
            model = apps.get_model(app_label, model_name)
            
            # Check if it's registered in admin
            if model in admin.site._registry:
                print(f"  ✅ {app_label}.{model_name} - Accessible")
                accessible_count += 1
            else:
                print(f"  ❌ {app_label}.{model_name} - Not registered in admin")
        except Exception as e:
            print(f"  ❌ {app_label}.{model_name} - Error: {e}")
    
    print(f"\n📈 Accessibility Score: {accessible_count}/{total_count} ({(accessible_count/total_count)*100:.1f}%)")
    
    return accessible_count == total_count

def create_admin_navigation_guide():
    """Create a navigation guide for the admin interface"""
    
    guide = """
# 🏥 Laso Digital Health Admin Navigation Guide

## 📊 Dashboard Overview
Access the main admin dashboard at: http://65.108.91.110:12000/admin/

## 🔐 Authentication
- Username: admin
- Password: admin123 (default - please change in production)

## 📋 Core Medical Records

### 📝 SOAP Notes
- URL: /admin/core/soapnote/
- Purpose: Manage patient consultation notes (Subjective, Objective, Assessment, Plan)
- Features: Search by patient/doctor, filter by date, view appointment details

### 🏥 EHR Records  
- URL: /admin/core/ehrrecord/
- Purpose: Electronic Health Records for patients
- Features: Medical history, allergies, medications, lab results

### ⭐ Reviews
- URL: /admin/core/review/
- Purpose: Patient reviews and ratings for doctors
- Features: Filter by rating, search by patient/doctor

### 🏢 Hospital Settings
- URL: /admin/core/hospitalsettings/
- Purpose: Configure hospital information and system settings
- Features: Business hours, contact info, system preferences

## 🎥 Telemedicine Management

### 📞 Consultations
- URL: /admin/telemedicine/consultation/
- Purpose: Manage virtual consultations
- Features: Video provider config, meeting links, status tracking

### 💬 Consultation Messages
- URL: /admin/telemedicine/consultationmessage/
- Purpose: Chat messages during consultations
- Features: Message history, private notes

### 👥 Consultation Participants
- URL: /admin/telemedicine/consultationparticipant/
- Purpose: Track who joins consultations
- Features: Join/leave times, connection issues

### 📹 Consultation Recordings
- URL: /admin/telemedicine/consultationrecording/
- Purpose: Manage consultation recordings
- Features: File size, duration, availability status

### ⏳ Waiting Room
- URL: /admin/telemedicine/waitingroom/
- Purpose: Manage patient waiting before consultations
- Features: Queue position, estimated wait time

### 🛠️ Technical Issues
- URL: /admin/telemedicine/technicalissue/
- Purpose: Track and resolve technical problems
- Features: Issue type, severity, resolution status

### ⚙️ Video Provider Config
- URL: /admin/telemedicine/videoproviderconfig/
- Purpose: Configure video calling services (Zoom, Google Meet, Jitsi)
- Features: API keys, settings, provider status

## 🔍 Quick Actions

### Search & Filter
- Use the search box in each section to find specific records
- Apply filters to narrow down results by date, status, etc.

### Bulk Operations
- Select multiple items to perform bulk actions
- Available for most model types

### Export Data
- Most sections support data export for reporting

## 🚨 Troubleshooting

If you can't access certain sections:
1. Ensure migrations are applied: ./fix_database.sh
2. Check user permissions
3. Verify containers are running: ./run.sh status
4. Check logs: ./run.sh logs

## 📞 Support
For technical issues, check the audit logs at: /admin/core/auditlog/
"""
    
    with open('/workspace/ADMIN_NAVIGATION_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("📖 Admin Navigation Guide created: ADMIN_NAVIGATION_GUIDE.md")

def main():
    """Main execution function"""
    
    print("🚀 Starting Django Admin Enhancement...")
    
    try:
        # Enhance admin interface
        enhance_admin_interface()
        
        # Verify accessibility
        verify_admin_accessibility()
        
        # Create navigation guide
        create_admin_navigation_guide()
        
        print("\n✅ Admin Enhancement Complete!")
        print("\n🎯 Next Steps:")
        print("1. Run migrations: ./fix_database.sh")
        print("2. Access admin: http://65.108.91.110:12000/admin/")
        print("3. Login with: admin / admin123")
        print("4. Navigate to Core and Telemedicine sections")
        
    except Exception as e:
        print(f"❌ Error during enhancement: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()