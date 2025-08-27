"""
Telemedicine Models for Laso Healthcare
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
from appointments.models import Appointment
import uuid
from datetime import datetime


class TelemedicineAppointment(models.Model):
    """
    Telemedicine appointment model
    """
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_patient_appointments',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_doctor_appointments',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    date = models.DateField(
        verbose_name=_('Date')
    )
    
    time = models.TimeField(
        verbose_name=_('Time')
    )
    
    duration = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Duration (minutes)')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Status')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    chief_complaint = models.TextField(
        blank=True,
        verbose_name=_('Chief Complaint')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_telemedicine_appointments',
        verbose_name=_('Created By')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Appointment')
        verbose_name_plural = _('Telemedicine Appointments')
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.patient} - Dr. {self.doctor} - {self.date} {self.time}"
    
    def is_past(self):
        """Is the appointment in the past?"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(datetime.combine(self.date, self.time))
        return appointment_datetime < now


class VideoSession(models.Model):
    """
    Video consultation session model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='video_sessions',
        verbose_name=_('Appointment')
    )
    
    room_name = models.CharField(
        max_length=255,
        verbose_name=_('Room Name')
    )
    
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='started_sessions',
        verbose_name=_('Started By')
    )
    
    start_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Start Time')
    )
    
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Time')
    )
    
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ended_sessions',
        verbose_name=_('Ended By')
    )
    
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Duration (seconds)')
    )
    
    recording_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Recording URL')
    )
    
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Fair')),
            ('poor', _('Poor')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Connection Quality')
    )
    
    class Meta:
        verbose_name = _('Video Session')
        verbose_name_plural = _('Video Sessions')
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Oturum: {self.appointment} - {self.start_time}"
    
    def get_duration(self):
        """Calculate session duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def save(self, *args, **kwargs):
        if self.end_time and not self.duration_seconds:
            self.duration_seconds = self.get_duration()
        super().save(*args, **kwargs)


class TelemedDocument(models.Model):
    """
    Telemedicine document model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Appointment')
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('lab_result', _('Lab Result')),
            ('prescription', _('Prescription')),
            ('medical_image', _('Medical Image')),
            ('referral', _('Sevk')),
            ('other', _('Other')),
        ],
        verbose_name=_('Document Type')
    )
    
    file = models.FileField(
        upload_to='telemedicine/documents/',
        verbose_name=_('File')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_telemedicine_documents',
        verbose_name=_('Uploaded By')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Document')
        verbose_name_plural = _('Telemedicine Documents')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.appointment}"


class TelemedPrescription(models.Model):
    """
    Telemedicine prescription model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Appointment')
    )
    
    medications = models.JSONField(
        verbose_name=_('Medications'),
        help_text=_('Medication list and dosage information')
    )
    
    instructions = models.TextField(
        verbose_name=_('Instructions')
    )
    
    duration_days = models.PositiveIntegerField(
        verbose_name=_('Duration (days)')
    )
    
    is_renewable = models.BooleanField(
        default=False,
        verbose_name=_('Renewable?')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_telemedicine_prescriptions',
        verbose_name=_('Prescribing Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Prescription')
        verbose_name_plural = _('Telemedicine Prescriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription: {self.appointment}"


class TelemedNote(models.Model):
    """
    Telemedicine note model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('Appointment')
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    
    content = models.TextField(
        verbose_name=_('Content')
    )
    
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('diagnosis', _('Diagnosis')),
            ('treatment_plan', _('Treatment Plan')),
            ('follow_up', _('Follow-up')),
            ('general', _('General Note')),
        ],
        default='general',
        verbose_name=_('Note Type')
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name=_('Private Note?'),
        help_text=_('Private notes can only be viewed by the doctor')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_telemedicine_notes',
        verbose_name=_('Created By')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Note')
        verbose_name_plural = _('Telemedicine Notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.appointment}"


class TeleMedicineConsultation(models.Model):
    """
    Remote healthcare consultation model
    """
    CONSULTATION_TYPE_CHOICES = [
        ('video', _('Video Call')),
        ('audio', _('Audio Call')),
        ('chat', _('Text Chat')),
        ('hybrid', _('Hybrid (Video + Chat)')),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', _('Zamanlandı')),
        ('waiting', _('Bekleniyor')),
        ('in_progress', _('Devam Ediyor')),
        ('completed', _('Tamamlandı')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
        ('technical_issue', _('Teknik Sorun')),
    ]
    
    # Temel bilgiler
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='telemedicine_consultation',
        verbose_name=_('Appointment')
    )
    
    consultation_type = models.CharField(
        max_length=20,
        choices=CONSULTATION_TYPE_CHOICES,
        default='video',
        verbose_name=_('Consultation Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Durum')
    )
    
    # Video conference information
    meeting_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_('Meeting ID')
    )
    
    meeting_url = models.URLField(
        blank=True,
        verbose_name=_('Meeting URL'),
        help_text=_('Video conference link')
    )
    
    meeting_password = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Meeting Password')
    )
    
    # Platform bilgileri
    platform = models.CharField(
        max_length=50,
        choices=[
            ('zoom', 'Zoom'),
            ('teams', 'Microsoft Teams'),
            ('meet', 'Google Meet'),
            ('webex', 'Cisco Webex'),
            ('internal', 'Internal System'),
        ],
        default='internal',
        verbose_name=_('Platform')
    )
    
    # Zaman bilgileri
    scheduled_start_time = models.DateTimeField(
        verbose_name=_('Scheduled Start')
    )
    
    actual_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Actual Start')
    )
    
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Time')
    )
    
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Duration (Minutes)')
    )
    
    # Participant information
    doctor_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Doctor Join Time')
    )
    
    patient_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Patient Join Time')
    )
    
    # Teknik detaylar
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Orta')),
            ('poor', _('Poor')),
        ],
        blank=True,
        verbose_name=_('Bağlantı Kalitesi')
    )
    
    technical_issues = models.TextField(
        blank=True,
        verbose_name=_('Technical Issues')
    )
    
    # Consultation details
    consultation_notes = models.TextField(
        blank=True,
        verbose_name=_('Consultation Notes')
    )
    
    # Backward compatibility field
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('General notes about the consultation')
    )
    
    patient_feedback = models.TextField(
        blank=True,
        verbose_name=_('Patient Feedback')
    )
    
    doctor_feedback = models.TextField(
        blank=True,
        verbose_name=_('Doctor Feedback')
    )
    
    # Rating system
    patient_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('Patient Rating (1-5)')
    )
    
    doctor_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('Doctor Rating (1-5)')
    )
    
    # Kayıt ve dosya paylaşımı
    is_recorded = models.BooleanField(
        default=False,
        verbose_name=_('Recording Made?')
    )
    
    recording_url = models.URLField(
        blank=True,
        verbose_name=_('Recording URL')
    )
    
    shared_files = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Shared Files'),
        help_text=_('List of files shared during consultation')
    )
    
    # Güvenlik ve gizlilik
    is_encrypted = models.BooleanField(
        default=True,
        verbose_name=_('Encrypted?')
    )
    
    waiting_room_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Waiting Room Active')
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Consultation')
        verbose_name_plural = _('Telemedicine Consultations')
        ordering = ['-scheduled_start_time']
    
    def __str__(self):
        return f"{self.appointment.patient} - {self.appointment.doctor} - {self.scheduled_start_time}"
    
    def get_duration(self):
        """Calculate consultation duration"""
        if self.actual_start_time and self.end_time:
            duration = self.end_time - self.actual_start_time
            return duration.total_seconds() / 60  # Dakika cinsinden
        return 0
    
    def is_active(self):
        """Is the consultation active?"""
        return self.status == 'in_progress'
    
    def can_join(self, user):
        """Can the user join the consultation?"""
        if self.status not in ['scheduled', 'waiting', 'in_progress']:
            return False
        
        # Only doctor and patient can join
        return user in [self.appointment.doctor, self.appointment.patient]
    
    def get_join_url(self):
        """Katılım URL'sini oluştur"""
        if self.meeting_url:
            return self.meeting_url
        
        # Internal sistem için URL oluştur
        return f"/telemedicine/join/{self.meeting_id}/"
    
    def mark_as_started(self, user):
        """Mark consultation as started"""
        if not self.actual_start_time:
            self.actual_start_time = timezone.now()
            self.status = 'in_progress'
            
            if user == self.appointment.doctor:
                self.doctor_joined_at = timezone.now()
            elif user == self.appointment.patient:
                self.patient_joined_at = timezone.now()
                
            self.save()
    
    def mark_as_completed(self):
        """Mark consultation as completed"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.status = 'completed'
            
            # Süreyi hesapla
            if self.actual_start_time:
                duration = self.end_time - self.actual_start_time
                self.duration_minutes = int(duration.total_seconds() / 60)
                
            self.save()


class TeleMedicineMessage(models.Model):
    """
    Telemedicine chat mesajları
    """
    consultation = models.ForeignKey(
        TeleMedicineConsultation,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name=_('Consultation')
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Sender')
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', _('Text')),
            ('file', _('File')),
            ('image', _('Image')),
            ('system', _('System Message')),
        ],
        default='text',
        verbose_name=_('Message Type')
    )
    
    content = models.TextField(
        verbose_name=_('Content')
    )
    
    file_url = models.URLField(
        blank=True,
        verbose_name=_('File URL')
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read?')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Time')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Message')
        verbose_name_plural = _('Telemedicine Messages')
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender} - {self.timestamp}"


class TeleMedicineSettings(models.Model):
    """
    Telemedicine ayarları
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_settings',
        verbose_name=_('User')
    )
    
    # Video settings
    default_camera_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Default Camera Enabled')
    )
    
    default_microphone_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Default Microphone Enabled')
    )
    
    video_quality = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Düşük (360p)')),
            ('medium', _('Orta (720p)')),
            ('high', _('Yüksek (1080p)')),
        ],
        default='medium',
        verbose_name=_('Video Quality')
    )
    
    # Bildirim ayarları
    consultation_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Consultation Reminders')
    )
    
    reminder_minutes_before = models.PositiveIntegerField(
        default=15,
        verbose_name=_('Remind Minutes Before')
    )
    
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Email Notifications')
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name=_('SMS Notifications')
    )
    
    # Güvenlik ayarları
    require_waiting_room = models.BooleanField(
        default=True,
        verbose_name=_('Waiting Room Required')
    )
    
    allow_recording = models.BooleanField(
        default=False,
        verbose_name=_('Recording Permission')
    )
    
    allow_file_sharing = models.BooleanField(
        default=True,
        verbose_name=_('Dosya Paylaşım İzni')
    )
    
    # Gelişmiş ayarlar
    max_consultation_duration = models.PositiveIntegerField(
        default=60,
        verbose_name=_('Maximum Consultation Duration (Minutes)')
    )
    
    auto_end_consultation = models.BooleanField(
        default=True,
        verbose_name=_('Auto End')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Settings')
        verbose_name_plural = _('Telemedicine Settings')
    
    def __str__(self):
        return f"{self.user} Settings"
