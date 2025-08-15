from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from bookings.models import Booking
import uuid
import json


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
    RESCHEDULED = 'rescheduled', 'Rescheduled'


class ConsultationType(models.TextChoices):
    INITIAL = 'initial', 'Initial Consultation'
    FOLLOW_UP = 'follow_up', 'Follow-up'
    EMERGENCY = 'emergency', 'Emergency'
    SECOND_OPINION = 'second_opinion', 'Second Opinion'
    ROUTINE_CHECKUP = 'routine_checkup', 'Routine Checkup'


class EnhancedConsultation(models.Model):
    """Enhanced consultation model with additional features"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE,
        related_name='consultation',
        null=True, blank=True
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
    
    # Enhanced consultation metadata
    consultation_type = models.CharField(
        max_length=20,
        choices=ConsultationType.choices,
        default=ConsultationType.INITIAL
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='normal'
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
    backup_meeting_url = models.URLField(blank=True, help_text="Backup meeting URL in case primary fails")
    
    # Enhanced scheduling
    status = models.CharField(
        max_length=20,
        choices=ConsultationStatus.choices,
        default=ConsultationStatus.SCHEDULED
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(180)],
        help_text="Estimated duration in minutes"
    )
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Enhanced technical details
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    recording_consent_doctor = models.BooleanField(default=False)
    recording_consent_patient = models.BooleanField(default=False)
    
    # Quality and feedback
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
    audio_quality = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Audio quality rating (1-5)"
    )
    video_quality = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Video quality rating (1-5)"
    )
    patient_satisfaction = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Patient satisfaction rating (1-5)"
    )
    
    # Enhanced documentation
    consultation_summary = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    prescription_issued = models.BooleanField(default=False)
    
    # Administrative fields
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to patient")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Billing and insurance
    is_billable = models.BooleanField(default=True)
    insurance_claim_submitted = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('declined', 'Declined'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_consultations'
    )
    
    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['scheduled_start']),
            models.Index(fields=['consultation_type']),
            models.Index(fields=['video_provider']),
            models.Index(fields=['priority']),
        ]
        permissions = [
            ('can_access_recordings', 'Can access consultation recordings'),
            ('can_view_all_consultations', 'Can view all consultations'),
            ('can_export_consultation_data', 'Can export consultation data'),
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
            now <= self.scheduled_start + timezone.timedelta(hours=2)
        )
    
    @property
    def is_overdue(self):
        """Check if consultation is overdue"""
        if self.status not in [ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING]:
            return False
        return timezone.now() > self.scheduled_start + timezone.timedelta(minutes=15)
    
    @property
    def can_record(self):
        """Check if consultation can be recorded"""
        return self.recording_consent_doctor and self.recording_consent_patient
    
    def get_duration_display(self):
        """Get human-readable duration"""
        if self.duration_minutes:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            if hours:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "N/A"
    
    def get_tags_list(self):
        """Get tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class ConsultationSession(models.Model):
    """Track individual sessions within a consultation (for reconnections)"""
    consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    participant_count = models.IntegerField(default=0)
    
    # Technical metrics
    max_participants = models.IntegerField(default=0)
    reconnection_count = models.IntegerField(default=0)
    technical_issues_count = models.IntegerField(default=0)
    average_connection_quality = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.session_id} for {self.consultation.id}"


class EnhancedConsultationParticipant(models.Model):
    """Enhanced participant tracking with detailed metrics"""
    consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    session = models.ForeignKey(
        ConsultationSession,
        on_delete=models.CASCADE,
        related_name='participants',
        null=True, blank=True
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
            ('assistant', 'Medical Assistant'),
            ('interpreter', 'Interpreter'),
            ('family', 'Family Member'),
        ]
    )
    
    # Participation tracking
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    total_duration_seconds = models.IntegerField(default=0)
    
    # Technical metrics
    connection_issues = models.IntegerField(default=0)
    audio_enabled_duration = models.IntegerField(default=0, help_text="Seconds with audio enabled")
    video_enabled_duration = models.IntegerField(default=0, help_text="Seconds with video enabled")
    screen_share_duration = models.IntegerField(default=0, help_text="Seconds screen sharing")
    
    # Device and browser info
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['consultation', 'user', 'session']
        indexes = [
            models.Index(fields=['consultation', 'role']),
            models.Index(fields=['joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} in {self.consultation.id}"


class ConsultationQualityMetrics(models.Model):
    """Detailed quality metrics for consultations"""
    consultation = models.OneToOneField(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='quality_metrics'
    )
    
    # Network quality
    average_latency_ms = models.IntegerField(null=True, blank=True)
    packet_loss_percentage = models.FloatField(null=True, blank=True)
    bandwidth_usage_mbps = models.FloatField(null=True, blank=True)
    
    # Audio/Video quality
    audio_bitrate_kbps = models.IntegerField(null=True, blank=True)
    video_bitrate_kbps = models.IntegerField(null=True, blank=True)
    video_resolution = models.CharField(max_length=20, blank=True)
    frame_rate = models.IntegerField(null=True, blank=True)
    
    # Stability metrics
    total_disconnections = models.IntegerField(default=0)
    longest_stable_period_seconds = models.IntegerField(null=True, blank=True)
    audio_dropouts = models.IntegerField(default=0)
    video_freezes = models.IntegerField(default=0)
    
    # Overall scores (1-10)
    overall_quality_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    user_experience_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quality metrics for {self.consultation.id}"


class ConsultationRecordingSegment(models.Model):
    """Track recording segments for consultations"""
    consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='recording_segments'
    )
    segment_id = models.CharField(max_length=255)
    file_url = models.URLField()
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Segment details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    video_quality = models.CharField(max_length=20, blank=True)
    audio_quality = models.CharField(max_length=20, blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Access control
    is_available = models.BooleanField(default=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['consultation', 'start_time']),
        ]
    
    def __str__(self):
        return f"Recording segment {self.segment_id} for {self.consultation.id}"


class ConsultationPrescription(models.Model):
    """Digital prescriptions issued during consultations"""
    consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    prescription_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Prescription details
    medications = models.JSONField(default=list, help_text="List of prescribed medications")
    instructions = models.TextField()
    duration = models.CharField(max_length=100, help_text="Treatment duration")
    
    # Digital signature
    doctor_signature = models.TextField(blank=True)
    digital_signature_hash = models.CharField(max_length=256, blank=True)
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('issued', 'Issued'),
            ('filled', 'Filled'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    
    issued_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    pharmacy_name = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consultation']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Prescription {self.prescription_id} for {self.consultation.id}"


class ConsultationFollowUp(models.Model):
    """Follow-up tracking for consultations"""
    original_consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='follow_ups'
    )
    follow_up_consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='follow_up_for',
        null=True, blank=True
    )
    
    # Follow-up details
    follow_up_type = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled Appointment'),
            ('check_in', 'Check-in Call'),
            ('test_results', 'Test Results Review'),
            ('medication_review', 'Medication Review'),
            ('symptoms_check', 'Symptoms Check'),
        ]
    )
    
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Follow-up content
    reason = models.TextField()
    notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_response', 'No Response'),
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_follow_ups'
    )
    
    class Meta:
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['original_consultation']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Follow-up for {self.original_consultation.id} - {self.follow_up_type}"


# Enhanced technical issue tracking
class EnhancedTechnicalIssue(models.Model):
    """Enhanced technical issue tracking with detailed diagnostics"""
    consultation = models.ForeignKey(
        EnhancedConsultation,
        on_delete=models.CASCADE,
        related_name='technical_issues'
    )
    issue_id = models.UUIDField(default=uuid.uuid4, unique=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    
    # Enhanced issue categorization
    issue_category = models.CharField(
        max_length=30,
        choices=[
            ('audio', 'Audio Problem'),
            ('video', 'Video Problem'),
            ('connection', 'Connection Issue'),
            ('screen_share', 'Screen Share Problem'),
            ('recording', 'Recording Issue'),
            ('browser', 'Browser Compatibility'),
            ('device', 'Device Issue'),
            ('performance', 'Performance Issue'),
            ('other', 'Other'),
        ]
    )
    
    # Detailed issue information
    title = models.CharField(max_length=200)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True)
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low - Minor inconvenience'),
            ('medium', 'Medium - Affects functionality'),
            ('high', 'High - Severely impacts consultation'),
            ('critical', 'Critical - Consultation cannot continue'),
        ],
        default='medium'
    )
    
    # Technical diagnostics
    browser_info = models.JSONField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    network_info = models.JSONField(null=True, blank=True)
    error_logs = models.TextField(blank=True)
    screenshot_url = models.URLField(blank=True)
    
    # Resolution tracking
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolution_time_minutes = models.IntegerField(null=True, blank=True)
    workaround_applied = models.TextField(blank=True)
    
    # Assignment and tracking
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_issues'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consultation']),
            models.Index(fields=['severity', 'resolved']),
            models.Index(fields=['issue_category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.consultation.id}"
    
    def get_resolution_time(self):
        """Calculate resolution time in minutes"""
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return int(delta.total_seconds() / 60)
        return None