#!/usr/bin/env python
"""
Test script for AI predictive analysis system
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.append(str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.ai_dashboard_service import get_ai_dashboard_service
from core.models_ai_config import AIConfiguration

User = get_user_model()

def test_ai_configuration():
    """Test AI configuration setup"""
    print("🔧 Testing AI Configuration...")
    
    try:
        # Create or get default AI configuration
        ai_config, created = AIConfiguration.objects.get_or_create(
            name='Default OpenRouter Config',
            defaults={
                'provider': 'openrouter',
                'model_name': 'deepseek/deepseek-chat-v3.1:free',
                'api_key': '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',
                'api_url': 'https://openrouter.ai/api/v1/chat/completions',
                'max_tokens': 1000,
                'temperature': 0.7,
                'is_active': True
            }
        )
        
        if created:
            print("✅ AI Configuration created successfully")
        else:
            print("✅ AI Configuration already exists")
            
        print(f"   Provider: {ai_config.provider}")
        print(f"   Model: {ai_config.model_name}")
        print(f"   Active: {ai_config.is_active}")
        
        return ai_config
        
    except Exception as e:
        print(f"❌ Error setting up AI configuration: {e}")
        return None

def test_patient_creation():
    """Create a test patient for AI analysis"""
    print("\n👤 Creating test patient...")
    
    try:
        # Create or get test patient
        patient, created = User.objects.get_or_create(
            username='test_patient_ai',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@test.com',
                'user_type': 'patient',
                'date_of_birth': '1980-01-01'
            }
        )
        
        if created:
            print("✅ Test patient created successfully")
        else:
            print("✅ Test patient already exists")
            
        print(f"   Name: {patient.get_full_name()}")
        print(f"   ID: {patient.id}")
        
        return patient
        
    except Exception as e:
        print(f"❌ Error creating test patient: {e}")
        return None

def test_vital_signs_creation(patient):
    """Create test vital signs for the patient"""
    print("\n📊 Creating test vital signs...")
    
    try:
        from treatments.models_vitals import VitalSign
        from django.utils import timezone
        
        # Create test vital signs
        vital_sign, created = VitalSign.objects.get_or_create(
            patient=patient,
            recorded_at=timezone.now(),
            defaults={
                'systolic_bp': 145,
                'diastolic_bp': 95,
                'heart_rate': 78,
                'temperature': 98.6,
                'weight': 180.0,
                'height': 70.0
            }
        )
        
        if created:
            print("✅ Test vital signs created successfully")
        else:
            print("✅ Test vital signs already exist")
            
        print(f"   Blood Pressure: {vital_sign.systolic_bp}/{vital_sign.diastolic_bp}")
        print(f"   Heart Rate: {vital_sign.heart_rate}")
        
        return vital_sign
        
    except Exception as e:
        print(f"❌ Error creating test vital signs: {e}")
        return None

def test_medical_history_creation(patient):
    """Create test medical history for the patient"""
    print("\n📋 Creating test medical history...")
    
    try:
        from treatments.models_medical_history import MedicalHistory
        from django.utils import timezone
        
        # Create test medical history
        history, created = MedicalHistory.objects.get_or_create(
            patient=patient,
            condition_name='Hypertension',
            defaults={
                'diagnosed_date': timezone.now().date(),
                'description': 'Stage 1 Hypertension',
                'is_active': True
            }
        )
        
        if created:
            print("✅ Test medical history created successfully")
        else:
            print("✅ Test medical history already exists")
            
        print(f"   Condition: {history.condition_name}")
        print(f"   Active: {history.is_active}")
        
        return history
        
    except Exception as e:
        print(f"❌ Error creating test medical history: {e}")
        return None

def test_cardiovascular_assessment(patient):
    """Test cardiovascular risk assessment"""
    print("\n❤️ Testing Cardiovascular Risk Assessment...")
    
    try:
        assessment = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
        
        print("✅ Cardiovascular assessment completed successfully")
        print(f"   Risk Level: {assessment['risk_assessment']['risk_level']}")
        print(f"   Risk Percentage: {assessment['risk_assessment']['risk_percentage']}%")
        print(f"   Confidence Level: {assessment['confidence_level']}%")
        
        # Print contributing factors
        print("   Contributing Factors:")
        for factor in assessment['contributing_factors']:
            print(f"     - {factor['name']}: {factor['score']}")
        
        return assessment
        
    except Exception as e:
        print(f"❌ Error in cardiovascular assessment: {e}")
        return None

def test_end_organ_assessment(patient):
    """Test end organ damage assessment"""
    print("\n🫀 Testing End Organ Damage Assessment...")
    
    try:
        assessment = get_ai_dashboard_service().generate_end_organ_damage_assessment(patient)
        
        print("✅ End organ damage assessment completed successfully")
        
        if assessment.get('prediction_results'):
            prediction = assessment['prediction_results']
            print(f"   Overall Risk: {prediction['overall_risk']['risk_level']}")
            print("   Organ-specific risks:")
            for organ, data in prediction['organ_risks'].items():
                print(f"     - {organ.title()}: {data['risk_level']}")
        else:
            print("   Assessment data prepared for analysis")
            
        return assessment
        
    except Exception as e:
        print(f"❌ Error in end organ assessment: {e}")
        return None

def test_ai_chat():
    """Test AI chat functionality"""
    print("\n🤖 Testing AI Chat Functionality...")
    
    try:
        from core.ai_service import get_ai_service
        
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username='test_doctor_ai',
            defaults={
                'first_name': 'Dr. Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.johnson@test.com',
                'user_type': 'doctor'
            }
        )
        
        # Test AI chat
        ai_service = get_ai_service()
        response = ai_service.chat(
            user=test_user,
            message="What are the key risk factors for cardiovascular disease in a 42-year-old patient with hypertension?"
        )
        
        if response['success']:
            print("✅ AI chat test successful")
            print(f"   Response length: {len(response['response'])} characters")
            print(f"   Tokens used: {response.get('tokens_used', 0)}")
            print(f"   Response time: {response.get('response_time', 0):.2f}s")
            print(f"   Preview: {response['response'][:100]}...")
        else:
            print(f"❌ AI chat test failed: {response.get('error', 'Unknown error')}")
            
        return response
        
    except Exception as e:
        print(f"❌ Error in AI chat test: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting AI Predictive Analysis System Tests")
    print("=" * 60)
    
    # Test AI configuration
    ai_config = test_ai_configuration()
    if not ai_config:
        print("❌ Cannot proceed without AI configuration")
        return
    
    # Test patient creation
    patient = test_patient_creation()
    if not patient:
        print("❌ Cannot proceed without test patient")
        return
    
    # Create test data
    vital_signs = test_vital_signs_creation(patient)
    medical_history = test_medical_history_creation(patient)
    
    # Test AI assessments
    cvd_assessment = test_cardiovascular_assessment(patient)
    organ_assessment = test_end_organ_assessment(patient)
    
    # Test AI chat
    chat_response = test_ai_chat()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   ✅ AI Configuration: {'✓' if ai_config else '✗'}")
    print(f"   ✅ Test Patient: {'✓' if patient else '✗'}")
    print(f"   ✅ Vital Signs: {'✓' if vital_signs else '✗'}")
    print(f"   ✅ Medical History: {'✓' if medical_history else '✗'}")
    print(f"   ✅ CVD Assessment: {'✓' if cvd_assessment else '✗'}")
    print(f"   ✅ Organ Assessment: {'✓' if organ_assessment else '✗'}")
    print(f"   ✅ AI Chat: {'✓' if chat_response and chat_response.get('success') else '✗'}")
    
    if all([ai_config, patient, cvd_assessment, organ_assessment]):
        print("\n🎉 All core tests passed! AI system is ready for use.")
        print("\n📝 Next steps:")
        print("   1. Access doctor AI dashboard: /ai/dashboard/doctor/")
        print("   2. Access admin AI dashboard: /ai/dashboard/admin/")
        print(f"   3. Run patient assessment: /ai/assessment/{patient.id}/")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()