#!/usr/bin/env python
"""
Test script for telemedicine functionality
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import User
from core.models_communication import Message, CommunicationNotification
from appointments.models import Appointment
from treatments.models import Treatment, Prescription, Medication
from treatments.models_medical_history import MedicalHistory
from telemedicine.models import TelemedicineAppointment, TelemedPrescription, TelemedNote

User = get_user_model()

def create_test_users():
    """Create test doctor and patient users"""
    print("Creating test users...")
    
    # Create doctor
    doctor, created = User.objects.get_or_create(
        username='test_doctor',
        defaults={
            'email': 'doctor@test.com',
            'first_name': 'Dr. John',
            'last_name': 'Smith',
            'user_type': 'doctor',
            'is_active': True,
        }
    )
    if created:
        doctor.set_password('testpass123')
        doctor.save()
        print(f"✓ Created doctor: {doctor.get_full_name()}")
    else:
        print(f"✓ Doctor already exists: {doctor.get_full_name()}")
    
    # Create patient
    patient, created = User.objects.get_or_create(
        username='test_patient',
        defaults={
            'email': 'patient@test.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'user_type': 'patient',
            'is_active': True,
        }
    )
    if created:
        patient.set_password('testpass123')
        patient.save()
        print(f"✓ Created patient: {patient.get_full_name()}")
    else:
        print(f"✓ Patient already exists: {patient.get_full_name()}")
    
    return doctor, patient

def create_test_medications():
    """Create test medications"""
    print("Creating test medications...")
    
    medications = [
        {
            'name': 'Amoxicillin 500mg',
            'active_ingredient': 'Amoxicillin',
            'drug_code': 'AMX500',
            'description': 'Antibiotic for bacterial infections',
            'side_effects': 'Nausea, diarrhea, allergic reactions',
            'contraindications': 'Penicillin allergy',
            'is_prescription': True
        },
        {
            'name': 'Ibuprofen 400mg',
            'active_ingredient': 'Ibuprofen',
            'drug_code': 'IBU400',
            'description': 'Anti-inflammatory pain reliever',
            'side_effects': 'Stomach upset, dizziness',
            'contraindications': 'Stomach ulcers, kidney disease',
            'is_prescription': False
        },
        {
            'name': 'Lisinopril 10mg',
            'active_ingredient': 'Lisinopril',
            'drug_code': 'LIS10',
            'description': 'ACE inhibitor for high blood pressure',
            'side_effects': 'Dry cough, dizziness, hyperkalemia',
            'contraindications': 'Pregnancy, angioedema history',
            'is_prescription': True
        }
    ]
    
    created_meds = []
    for med_data in medications:
        medication, created = Medication.objects.get_or_create(
            name=med_data['name'],
            defaults=med_data
        )
        created_meds.append(medication)
        if created:
            print(f"✓ Created medication: {medication.name}")
        else:
            print(f"✓ Medication already exists: {medication.name}")
    
    return created_meds

def create_test_appointment(doctor, patient):
    """Create test appointment"""
    print("Creating test appointment...")
    
    appointment, created = Appointment.objects.get_or_create(
        patient=patient,
        doctor=doctor,
        date=timezone.now().date() + timedelta(days=1),
        time=timezone.now().time().replace(hour=14, minute=0, second=0, microsecond=0),
        defaults={
            'status': 'scheduled',
            'appointment_type': 'consultation',
            'notes': 'Test telemedicine appointment',
            'created_by': doctor
        }
    )
    
    if created:
        print(f"✓ Created appointment: {appointment}")
    else:
        print(f"✓ Appointment already exists: {appointment}")
    
    return appointment

def create_telemedicine_appointment(doctor, patient):
    """Create telemedicine appointment"""
    print("Creating telemedicine appointment...")
    
    telemed_appointment, created = TelemedicineAppointment.objects.get_or_create(
        patient=patient,
        doctor=doctor,
        date=timezone.now().date() + timedelta(days=1),
        time=timezone.now().time().replace(hour=15, minute=0, second=0, microsecond=0),
        defaults={
            'status': 'scheduled',
            'description': 'Test telemedicine consultation',
            'chief_complaint': 'Follow-up consultation',
            'created_by': doctor
        }
    )
    
    if created:
        print(f"✓ Created telemedicine appointment: {telemed_appointment}")
    else:
        print(f"✓ Telemedicine appointment already exists: {telemed_appointment}")
    
    return telemed_appointment

def test_messaging(doctor, patient):
    """Test doctor-patient messaging"""
    print("\n=== Testing Messaging System ===")
    
    # Doctor sends message to patient
    message = Message.objects.create(
        sender=doctor,
        receiver=patient,
        subject="Test Message from Doctor",
        content="Hello, this is a test message from your doctor. Please reply when you receive this."
    )
    print(f"✓ Doctor sent message: {message.subject}")
    
    # Create notification for patient
    notification = CommunicationNotification.objects.create(
        user=patient,
        notification_type='message',
        title='New Message from Dr. Smith',
        message=f'You have received a new message: {message.subject}',
        related_url=f'/messages/{message.id}/'
    )
    print(f"✓ Created notification for patient: {notification.title}")
    
    # Patient replies
    reply = Message.objects.create(
        sender=patient,
        receiver=doctor,
        subject="Re: Test Message from Doctor",
        content="Thank you for your message, Doctor. I received it successfully.",
        parent_message=message
    )
    print(f"✓ Patient replied: {reply.subject}")
    
    # Create notification for doctor
    doctor_notification = CommunicationNotification.objects.create(
        user=doctor,
        notification_type='message',
        title='Reply from Jane Doe',
        message=f'You have received a reply: {reply.subject}',
        related_url=f'/messages/{reply.id}/'
    )
    print(f"✓ Created notification for doctor: {doctor_notification.title}")
    
    return message, reply

def test_prescriptions(doctor, patient, medications, telemed_appointment):
    """Test prescription functionality"""
    print("\n=== Testing Prescription System ===")
    
    # Create telemedicine prescription
    prescription_data = {
        'medication_1': {
            'name': medications[0].name,
            'dosage': '500mg',
            'frequency': 'Twice daily',
            'duration': '7 days'
        },
        'medication_2': {
            'name': medications[1].name,
            'dosage': '400mg',
            'frequency': 'As needed',
            'duration': '5 days'
        }
    }
    
    telemed_prescription = TelemedPrescription.objects.create(
        appointment=telemed_appointment,
        medications=prescription_data,
        instructions="Take with food. Complete the full course of antibiotics.",
        duration_days=7,
        is_renewable=False,
        created_by=doctor
    )
    print(f"✓ Created telemedicine prescription: {telemed_prescription}")
    
    # Create notification for patient about prescription
    prescription_notification = CommunicationNotification.objects.create(
        user=patient,
        notification_type='prescription',
        title='New Prescription Available',
        message=f'Dr. {doctor.get_full_name()} has prescribed new medications for you.',
        related_url=f'/prescriptions/{telemed_prescription.id}/'
    )
    print(f"✓ Created prescription notification: {prescription_notification.title}")
    
    return telemed_prescription

def test_medical_records(patient, doctor):
    """Test medical records access"""
    print("\n=== Testing Medical Records Access ===")
    
    # Create medical history record
    medical_history = MedicalHistory.objects.create(
        patient=patient,
        condition='Hypertension',
        diagnosis_date=timezone.now().date() - timedelta(days=30),
        status='active',
        notes='Patient diagnosed with mild hypertension. Currently on medication.',
        diagnosed_by=doctor
    )
    print(f"✓ Created medical history: {medical_history.condition}")
    
    # Create treatment record
    # First create a regular appointment for the treatment
    past_appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=timezone.now().date() - timedelta(days=7),
        time=timezone.now().time().replace(hour=10, minute=0, second=0, microsecond=0),
        status='completed',
        appointment_type='consultation',
        notes='Follow-up for hypertension',
        created_by=doctor
    )
    
    treatment = Treatment.objects.create(
        appointment=past_appointment,
        diagnosis='Hypertension - well controlled',
        notes='Patient responding well to current medication. Continue current treatment plan.'
    )
    print(f"✓ Created treatment record: {treatment.diagnosis}")
    
    # Create prescription for the treatment
    prescription = Prescription.objects.create(
        treatment=treatment,
        name='Lisinopril 10mg',
        dosage='10mg once daily',
        instructions='Take in the morning with or without food. Monitor blood pressure regularly.'
    )
    print(f"✓ Created prescription: {prescription.name}")
    
    return medical_history, treatment, prescription

def verify_data_access():
    """Verify that data can be accessed correctly"""
    print("\n=== Verifying Data Access ===")
    
    # Get test users
    try:
        doctor = User.objects.get(username='test_doctor')
        patient = User.objects.get(username='test_patient')
        print(f"✓ Found doctor: {doctor.get_full_name()}")
        print(f"✓ Found patient: {patient.get_full_name()}")
    except User.DoesNotExist:
        print("✗ Test users not found")
        return False
    
    # Check messages
    messages = Message.objects.filter(
        models.Q(sender=doctor, receiver=patient) | 
        models.Q(sender=patient, receiver=doctor)
    )
    print(f"✓ Found {messages.count()} messages between doctor and patient")
    
    # Check notifications
    patient_notifications = CommunicationNotification.objects.filter(user=patient)
    doctor_notifications = CommunicationNotification.objects.filter(user=doctor)
    print(f"✓ Patient has {patient_notifications.count()} notifications")
    print(f"✓ Doctor has {doctor_notifications.count()} notifications")
    
    # Check prescriptions
    telemed_prescriptions = TelemedPrescription.objects.filter(
        appointment__patient=patient,
        appointment__doctor=doctor
    )
    print(f"✓ Found {telemed_prescriptions.count()} telemedicine prescriptions")
    
    # Check medical records
    medical_records = MedicalHistory.objects.filter(patient=patient)
    treatments = Treatment.objects.filter(appointment__patient=patient)
    print(f"✓ Patient has {medical_records.count()} medical history records")
    print(f"✓ Patient has {treatments.count()} treatment records")
    
    return True

def main():
    """Main test function"""
    print("🏥 Starting Telemedicine Functionality Tests")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Create test data
            doctor, patient = create_test_users()
            medications = create_test_medications()
            appointment = create_test_appointment(doctor, patient)
            telemed_appointment = create_telemedicine_appointment(doctor, patient)
            
            # Test functionality
            message, reply = test_messaging(doctor, patient)
            prescription = test_prescriptions(doctor, patient, medications, telemed_appointment)
            medical_history, treatment, regular_prescription = test_medical_records(patient, doctor)
            
            # Verify data access
            success = verify_data_access()
            
            if success:
                print("\n🎉 All tests completed successfully!")
                print("\nTest Summary:")
                print(f"- Doctor: {doctor.username} ({doctor.email})")
                print(f"- Patient: {patient.username} ({patient.email})")
                print(f"- Messages: Doctor → Patient, Patient → Doctor")
                print(f"- Prescriptions: {prescription.medications}")
                print(f"- Medical Records: {medical_history.condition}")
                print(f"- Treatment: {treatment.diagnosis}")
                
                print("\nTo test in the web interface:")
                print("1. Login as doctor: test_doctor / testpass123")
                print("2. Login as patient: test_patient / testpass123")
                print("3. Check dashboards for messages, prescriptions, and medical records")
                
            else:
                print("\n❌ Some tests failed!")
                
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()