from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SoapNote, EHRRecord, AuditLog
from bookings.models import Booking

User = get_user_model()


class SoapNoteSerializer(serializers.ModelSerializer):
    """Serializer for SOAP Notes"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='appointment.appointment_time', read_only=True)
    
    class Meta:
        model = SoapNote
        fields = [
            'id', 'patient', 'patient_name', 'appointment', 'appointment_date', 
            'appointment_time', 'created_by', 'doctor_name', 'subjective', 
            'objective', 'assessment', 'plan', 'created_at', 'updated_at', 'is_draft'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient_name', 'doctor_name', 'appointment_date', 'appointment_time']

    def validate(self, data):
        """Validate SOAP note data"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        user = request.user
        
        # Ensure only doctors can create SOAP notes
        if user.role != 'doctor':
            raise serializers.ValidationError("Only doctors can create SOAP notes")
        
        # Ensure the appointment belongs to the doctor
        appointment = data.get('appointment')
        if appointment and appointment.doctor != user:
            raise serializers.ValidationError("You can only create SOAP notes for your own appointments")
        
        # Ensure the patient matches the appointment
        patient = data.get('patient')
        if patient and appointment and appointment.patient != patient:
            raise serializers.ValidationError("Patient must match the appointment")
        
        # Set the created_by field to the current user
        data['created_by'] = user
        
        return data

    def create(self, validated_data):
        """Create a new SOAP note"""
        return SoapNote.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing SOAP note"""
        # Remove fields that shouldn't be updated
        validated_data.pop('patient', None)
        validated_data.pop('appointment', None)
        validated_data.pop('created_by', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SoapNoteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for SOAP note lists"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    
    class Meta:
        model = SoapNote
        fields = [
            'id', 'patient_name', 'doctor_name', 'appointment_date', 
            'created_at', 'updated_at', 'is_draft'
        ]


class EHRRecordSerializer(serializers.ModelSerializer):
    """Serializer for EHR Records"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    last_updated_by_name = serializers.CharField(source='last_updated_by.get_full_name', read_only=True)
    soap_notes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EHRRecord
        fields = [
            'id', 'patient', 'patient_name', 'allergies', 'medications', 
            'medical_history', 'immunizations', 'lab_results', 'imaging_results',
            'vital_signs_history', 'emergency_contacts', 'insurance_info',
            'created_at', 'updated_at', 'last_updated_by', 'last_updated_by_name',
            'soap_notes_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient_name', 'last_updated_by_name', 'soap_notes_count']

    def get_soap_notes_count(self, obj):
        """Get count of SOAP notes for this patient"""
        return obj.patient.soap_notes.count()

    def validate(self, data):
        """Validate EHR record data"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        user = request.user
        
        # Set the last_updated_by field
        data['last_updated_by'] = user
        
        return data

    def create(self, validated_data):
        """Create a new EHR record"""
        return EHRRecord.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing EHR record"""
        # Remove fields that shouldn't be updated
        validated_data.pop('patient', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EHRRecordListSerializer(serializers.ModelSerializer):
    """Simplified serializer for EHR record lists"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    soap_notes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EHRRecord
        fields = [
            'id', 'patient_name', 'allergies', 'medications', 
            'medical_history', 'immunizations', 'created_at', 'updated_at',
            'soap_notes_count'
        ]

    def get_soap_notes_count(self, obj):
        """Get count of SOAP notes for this patient"""
        return obj.patient.soap_notes.count()


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for Audit Logs (read-only)"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'model_name', 'object_id',
            'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = '__all__'


class PatientSearchSerializer(serializers.ModelSerializer):
    """Serializer for patient search results"""
    profile = serializers.SerializerMethodField()
    has_ehr = serializers.SerializerMethodField()
    last_appointment = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile', 'has_ehr', 'last_appointment']
    
    def get_profile(self, obj):
        """Get patient profile information"""
        if hasattr(obj, 'profile'):
            return {
                'phone': obj.profile.phone,
                'dob': obj.profile.dob,
                'gender': obj.profile.gender,
                'city': obj.profile.city,
                'blood_group': obj.profile.blood_group,
            }
        return {}
    
    def get_has_ehr(self, obj):
        """Check if patient has EHR record"""
        return hasattr(obj, 'ehr_record')
    
    def get_last_appointment(self, obj):
        """Get last appointment information"""
        last_appointment = obj.patient_appointments.order_by('-appointment_date').first()
        if last_appointment:
            return {
                'date': last_appointment.appointment_date,
                'status': last_appointment.status,
                'doctor_name': last_appointment.doctor.get_full_name(),
            }
        return None
