from rest_framework import serializers
from django.utils import timezone
from .models import (
    Consultation, ConsultationMessage, ConsultationParticipant,
    ConsultationRecording, WaitingRoom, TechnicalIssue,
    VideoProvider, ConsultationStatus
)
from bookings.models import Booking
from accounts.models import User


class ConsultationSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    appointment_date = serializers.DateField(source='booking.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='booking.appointment_time', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_start = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'booking_id', 'doctor_name', 'patient_name',
            'appointment_date', 'appointment_time', 'video_provider',
            'meeting_id', 'meeting_url', 'meeting_password', 'status',
            'scheduled_start', 'actual_start', 'actual_end',
            'duration_minutes', 'recording_enabled', 'recording_url',
            'connection_quality', 'notes', 'created_at', 'updated_at',
            'is_active', 'can_start'
        ]
        read_only_fields = [
            'id', 'booking_id', 'doctor_name', 'patient_name',
            'appointment_date', 'appointment_time', 'actual_start',
            'actual_end', 'duration_minutes', 'created_at', 'updated_at',
            'is_active', 'can_start'
        ]


class ConsultationCreateSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'booking_id', 'video_provider', 'recording_enabled', 'notes'
        ]
    
    def validate_booking_id(self, value):
        """Validate that booking exists and doesn't already have a consultation"""
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        
        if hasattr(booking, 'consultation'):
            raise serializers.ValidationError("Consultation already exists for this booking")
        
        if booking.status in ['cancelled', 'completed']:
            raise serializers.ValidationError("Cannot create consultation for cancelled or completed booking")
        
        return value
    
    def create(self, validated_data):
        booking_id = validated_data.pop('booking_id')
        booking = Booking.objects.get(id=booking_id)
        
        # Create consultation with booking details
        consultation = Consultation.objects.create(
            booking=booking,
            doctor=booking.doctor,
            patient=booking.patient,
            scheduled_start=timezone.datetime.combine(
                booking.appointment_date,
                booking.appointment_time,
                timezone.get_current_timezone()
            ),
            **validated_data
        )
        
        # Generate meeting details based on provider
        consultation = self._generate_meeting_details(consultation)
        return consultation
    
    def _generate_meeting_details(self, consultation):
        """Generate meeting details based on video provider"""
        if consultation.video_provider == VideoProvider.JITSI:
            # Generate Jitsi meeting room
            room_name = f"laso-consultation-{consultation.id}"
            consultation.meeting_id = room_name
            consultation.meeting_url = f"https://meet.jit.si/{room_name}"
        
        elif consultation.video_provider == VideoProvider.ZOOM:
            # TODO: Implement Zoom meeting creation via API
            consultation.meeting_id = f"zoom-{consultation.id}"
            consultation.meeting_url = "https://zoom.us/j/placeholder"
        
        elif consultation.video_provider == VideoProvider.GOOGLE_MEET:
            # TODO: Implement Google Meet meeting creation via API
            consultation.meeting_id = f"meet-{consultation.id}"
            consultation.meeting_url = "https://meet.google.com/placeholder"
        
        consultation.save()
        return consultation


class ConsultationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    
    class Meta:
        model = ConsultationMessage
        fields = [
            'id', 'message', 'message_type', 'timestamp',
            'is_private', 'sender_name', 'sender_role'
        ]
        read_only_fields = ['id', 'timestamp', 'sender_name', 'sender_role']


class ConsultationParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ConsultationParticipant
        fields = [
            'id', 'user_name', 'user_email', 'role',
            'joined_at', 'left_at', 'connection_issues'
        ]
        read_only_fields = ['id', 'user_name', 'user_email']


class ConsultationRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationRecording
        fields = [
            'id', 'recording_id', 'recording_url', 'download_url',
            'file_size_mb', 'duration_seconds', 'expires_at',
            'is_processed', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WaitingRoomSerializer(serializers.ModelSerializer):
    consultation_id = serializers.UUIDField(source='consultation.id', read_only=True)
    patient_name = serializers.CharField(source='consultation.patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='consultation.doctor.get_full_name', read_only=True)
    
    class Meta:
        model = WaitingRoom
        fields = [
            'id', 'consultation_id', 'patient_name', 'doctor_name',
            'patient_joined_at', 'doctor_notified_at',
            'estimated_wait_minutes', 'queue_position'
        ]
        read_only_fields = ['id', 'consultation_id', 'patient_name', 'doctor_name']


class TechnicalIssueSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='reporter.get_full_name', read_only=True)
    consultation_id = serializers.UUIDField(source='consultation.id', read_only=True)
    
    class Meta:
        model = TechnicalIssue
        fields = [
            'id', 'consultation_id', 'reporter_name', 'issue_type',
            'description', 'severity', 'resolved', 'resolution_notes',
            'created_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'consultation_id', 'reporter_name', 'created_at']


class ConsultationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for consultation lists"""
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='booking.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='booking.appointment_time', read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'doctor_name', 'patient_name', 'appointment_date',
            'appointment_time', 'status', 'video_provider',
            'scheduled_start', 'duration_minutes', 'created_at'
        ]


class ConsultationActionSerializer(serializers.Serializer):
    """Serializer for consultation actions (start, end, etc.)"""
    action = serializers.ChoiceField(choices=['start', 'end', 'cancel'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        consultation = self.context.get('consultation')
        user = self.context.get('user')
        
        if not consultation or not user:
            raise serializers.ValidationError("Invalid context")
        
        if value == 'start':
            if user.role != 'doctor':
                raise serializers.ValidationError("Only doctors can start consultations")
            if not consultation.can_start:
                raise serializers.ValidationError("Consultation cannot be started at this time")
        
        elif value == 'end':
            if user.role != 'doctor':
                raise serializers.ValidationError("Only doctors can end consultations")
            if consultation.status != ConsultationStatus.IN_PROGRESS:
                raise serializers.ValidationError("Consultation is not in progress")
        
        elif value == 'cancel':
            if user.id not in [consultation.doctor.id, consultation.patient.id]:
                raise serializers.ValidationError("Only participants can cancel consultations")
            if consultation.status in [ConsultationStatus.COMPLETED, ConsultationStatus.CANCELLED]:
                raise serializers.ValidationError("Consultation cannot be cancelled")
        
        return value


class VideoProviderChoicesSerializer(serializers.Serializer):
    """Serializer for video provider choices"""
    value = serializers.CharField()
    label = serializers.CharField()


class ConsultationStatsSerializer(serializers.Serializer):
    """Serializer for consultation statistics"""
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    active_consultations = serializers.IntegerField()
    average_duration = serializers.FloatField()
    total_duration = serializers.IntegerField()
    by_provider = serializers.DictField()
    by_status = serializers.DictField()