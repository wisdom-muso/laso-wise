from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import SoapNote, EHRRecord, AuditLog, Speciality, Review
from accounts.models import User
from bookings.models import Booking

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'full_name']
        read_only_fields = ['id', 'username', 'email', 'role', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class SpecialitySerializer(serializers.ModelSerializer):
    """Serializer for Speciality model"""
    doctor_count = serializers.ReadOnlyField()
    image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Speciality
        fields = ['id', 'name', 'slug', 'description', 'image', 'image_url', 'is_active', 'doctor_count']
        read_only_fields = ['id', 'slug', 'doctor_count', 'image_url']

class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    patient = UserBasicSerializer(read_only=True)
    doctor = UserBasicSerializer(read_only=True)
    rating_percent = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = ['id', 'patient', 'doctor', 'booking', 'rating', 'review', 'rating_percent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'patient', 'doctor', 'rating_percent', 'created_at', 'updated_at']

class SoapNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for SOAP Notes
    """
    patient = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = SoapNote
        fields = [
            'id', 'patient', 'appointment', 'created_by',
            'subjective', 'objective', 'assessment', 'plan',
            'notes', 'is_draft', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Custom validation for SOAP notes"""
        if not data.get('subjective') and not data.get('objective') and not data.get('assessment') and not data.get('plan'):
            raise serializers.ValidationError("At least one SOAP section must be filled.")
        return data

class SoapNoteListSerializer(serializers.ModelSerializer):
    """
    Simplified SOAP Note serializer for list views
    """
    patient_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    appointment_date = serializers.SerializerMethodField()
    
    class Meta:
        model = SoapNote
        fields = [
            'id', 'patient_name', 'created_by_name', 'appointment_date',
            'subjective', 'is_draft', 'created_at'
        ]
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name() if obj.patient else ""
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ""
    
    def get_appointment_date(self, obj):
        return obj.appointment.date if obj.appointment else None

class EHRRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for EHR Records
    """
    patient = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = EHRRecord
        fields = [
            'id', 'patient', 'created_by', 'medical_history',
            'allergies', 'current_medications', 'family_history',
            'social_history', 'immunizations', 'vital_signs',
            'lab_results', 'imaging_results', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'created_by', 'created_at', 'updated_at']

class EHRRecordListSerializer(serializers.ModelSerializer):
    """
    Simplified EHR Record serializer for list views
    """
    patient_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EHRRecord
        fields = [
            'id', 'patient_name', 'created_by_name',
            'created_at', 'updated_at'
        ]
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name() if obj.patient else ""
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ""

class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for Audit Logs
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'model_name', 'object_id',
            'object_repr', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class PatientSearchSerializer(serializers.Serializer):
    """
    Serializer for patient search
    """
    query = serializers.CharField(max_length=100, required=True)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
