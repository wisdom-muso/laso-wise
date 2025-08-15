from django.db import models
from django.conf import settings
from django.utils import timezone
from bookings.models import Booking
import uuid


class VideoProvider(models.TextChoices):
    ZOOM = 'zoom', 'Zoom'
    GOOGLE_MEET = 'google_meet', 'Google Meet'
    JITSI = 'jitsi', 'Jitsi'


class ConsultationStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    WAITING = 'waiting', 'Waiting Room'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'


class Consultation(models.Model):
    """
    Virtual consultation linked to appointment booking
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE,
        related_name='consultation'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_doctor',
        limit_choices_to={'role': 'doctor'}
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_patient',
        limit_choices_to={'role': 'patient'}
    )
    
    # Video call configuration
    video_provider = models.CharField(
        max_length=20,
        choices=VideoProvider.choices,
        default=VideoProvider.JITSI
    )
    meeting_id = models.CharField(max_length=255, blank=True)
    meeting_url = models.URLField(blank=True)
    meeting_password = models.CharField(max_length=100, blank=True)
    
    # Consultation details
    status = models.CharField(
        max_length=20,
        choices=ConsultationStatus.choices,
        default=ConsultationStatus.SCHEDULED
    )
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Technical details
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['scheduled_start']),
        ]
    
    def __str__(self):
        return f"Consultation {self.id} - {self.doctor.get_full_name()} with {self.patient.get_full_name()}"
    
    @property
    def is_active(self):
        return self.status in [ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]
    
    @property
    def can_start(self):
        """Check if consultation can be started"""
        now = timezone.now()
        return (
            self.status == ConsultationStatus.SCHEDULED and
            now >= self.scheduled_start - timezone.timedelta(minutes=15) and
            now <= self.scheduled_start + timezone.timedelta(hours=1)
        )
    
    def start_consultation(self):
        """Start the consultation"""
        if self.can_start:
            self.status = ConsultationStatus.IN_PROGRESS
            self.actual_start = timezone.now()
            self.save()
            return True
        return False
    
    def end_consultation(self):
        """End the consultation"""
        if self.status == ConsultationStatus.IN_PROGRESS:
            self.actual_end = timezone.now()
            self.status = ConsultationStatus.COMPLETED
            if self.actual_start:
                duration = self.actual_end - self.actual_start
                self.duration_minutes = int(duration.total_seconds() / 60)
            self.save()
            
            # Update booking status
            self.booking.status = 'completed'
            self.booking.save()
            return True
        return False


class ConsultationParticipant(models.Model):
    """
    Track participants in a consultation (for group consultations or observers)
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ('doctor', 'Doctor'),
            ('patient', 'Patient'),
            ('observer', 'Observer'),
            ('assistant', 'Assistant'),
        ]
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    connection_issues = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['consultation', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} in {self.consultation.id}"


class ConsultationMessage(models.Model):
    """
    Chat messages during consultation
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Message'),
            ('system', 'System Message'),
            ('file', 'File Share'),
            ('prescription', 'Prescription'),
        ],
        default='text'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)  # Only visible to medical staff
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.timestamp}"


class ConsultationRecording(models.Model):
    """
    Recording metadata for consultations
    """
    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name='recording'
    )
    recording_id = models.CharField(max_length=255)  # Provider-specific ID
    recording_url = models.URLField()
    download_url = models.URLField(blank=True)
    file_size_mb = models.FloatField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Access control
    expires_at = models.DateTimeField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Recording for {self.consultation.id}"


class WaitingRoom(models.Model):
    """
    Virtual waiting room for patients before consultation
    """
    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name='waiting_room'
    )
    patient_joined_at = models.DateTimeField(null=True, blank=True)
    doctor_notified_at = models.DateTimeField(null=True, blank=True)
    estimated_wait_minutes = models.IntegerField(default=0)
    queue_position = models.IntegerField(default=1)
    
    def __str__(self):
        return f"Waiting room for {self.consultation.id}"


class TechnicalIssue(models.Model):
    """
    Log technical issues during consultations
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='technical_issues'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    issue_type = models.CharField(
        max_length=30,
        choices=[
            ('audio', 'Audio Problem'),
            ('video', 'Video Problem'),
            ('connection', 'Connection Issue'),
            ('screen_share', 'Screen Share Problem'),
            ('recording', 'Recording Issue'),
            ('other', 'Other'),
        ]
    )
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.issue_type} issue in {self.consultation.id}"


class VideoProviderConfig(models.Model):
    """
    Configuration for different video providers
    """
    provider = models.CharField(
        max_length=20,
        choices=VideoProvider.choices,
        unique=True
    )
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    webhook_url = models.URLField(blank=True)
    max_participants = models.IntegerField(default=2)
    recording_enabled = models.BooleanField(default=True)
    
    # Provider-specific settings (JSON field would be better, but keeping simple)
    settings_json = models.TextField(blank=True, help_text="JSON configuration for provider-specific settings")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.provider} configuration"