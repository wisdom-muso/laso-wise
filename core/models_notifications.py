"""
Advanced Notification System for Laso Healthcare
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class NotificationType(models.TextChoices):
    """Notification types"""
    APPOINTMENT_REMINDER = 'appointment_reminder', _('Appointment Reminder')
    APPOINTMENT_CANCELLED = 'appointment_cancelled', _('Appointment Cancelled')
    APPOINTMENT_CONFIRMED = 'appointment_confirmed', _('Appointment Confirmed')
    LAB_RESULT_READY = 'lab_result_ready', _('Lab Result Ready')
    PRESCRIPTION_READY = 'prescription_ready', _('Prescription Ready')
    TREATMENT_COMPLETED = 'treatment_completed', _('Treatment Completed')
    MEDICATION_REMINDER = 'medication_reminder', _('Medication Reminder')
    SYSTEM_MAINTENANCE = 'system_maintenance', _('System Maintenance')
    DOCTOR_SCHEDULE_CHANGE = 'doctor_schedule_change', _('Doctor Schedule Change')
    EMERGENCY_ALERT = 'emergency_alert', _('Emergency Alert')


class NotificationPriority(models.TextChoices):
    """Notification priority levels"""
    LOW = 'low', _('Low')
    NORMAL = 'normal', _('Normal')
    HIGH = 'high', _('High')
    URGENT = 'urgent', _('Urgent')


class Notification(models.Model):
    """
    Gelişmiş bildirim modeli
    """
    # Recipient - Use null=True for migration purposes
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient'),
        null=True
    )
    
    # Sender (optional, can be None for system notifications)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True,
        verbose_name=_('Sender')
    )
    
    # Notification details
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        verbose_name=_('Notification Type')
    )
    
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name=_('Priority')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title')
    )
    
    message = models.TextField(
        verbose_name=_('Message')
    )
    
    # İlişkili nesne (Generic Foreign Key ile herhangi bir modele bağlanabilir)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read?')
    )
    
    is_sent_via_email = models.BooleanField(
        default=False,
        verbose_name=_('Sent via Email?')
    )
    
    is_sent_via_sms = models.BooleanField(
        default=False,
        verbose_name=_('Sent via SMS?')
    )
    
    # Timing
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At')
    )
    
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Scheduled For')
    )
    
    # Extra data (in JSON format)
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Extra Data')
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.recipient} - {self.title}"
    
    def mark_as_read(self):
        """Bildirimi okundu olarak işaretle"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_priority_color(self):
        """Öncelik seviyesine göre renk döndür"""
        colors = {
            'low': 'secondary',
            'normal': 'primary', 
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'primary')
    
    def get_icon(self):
        """Bildirim türüne göre ikon döndür"""
        icons = {
            'appointment_reminder': 'calendar-alt',
            'appointment_cancelled': 'calendar-times',
            'appointment_confirmed': 'calendar-check',
            'lab_result_ready': 'flask',
            'prescription_ready': 'pills',
            'treatment_completed': 'check-circle',
            'medication_reminder': 'clock',
            'system_maintenance': 'tools',
            'doctor_schedule_change': 'user-md',
            'emergency_alert': 'exclamation-triangle'
        }
        return icons.get(self.notification_type, 'bell')


class NotificationPreference(models.Model):
    """
    User notification preferences
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('User')
    )
    
    # Email notifications
    email_appointment_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Appointment reminders (Email)')
    )
    
    email_lab_results = models.BooleanField(
        default=True,
        verbose_name=_('Lab results (Email)')
    )
    
    email_prescription_ready = models.BooleanField(
        default=True,
        verbose_name=_('Prescription ready (Email)')
    )
    
    email_system_updates = models.BooleanField(
        default=False,
        verbose_name=_('System updates (Email)')
    )
    
    # SMS notifications
    sms_appointment_reminders = models.BooleanField(
        default=False,
        verbose_name=_('Appointment reminders (SMS)')
    )
    
    sms_emergency_alerts = models.BooleanField(
        default=True,
        verbose_name=_('Emergency alerts (SMS)')
    )
    
    # Push notifications
    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Push notifications')
    )
    
    # Reminder times
    appointment_reminder_hours = models.PositiveIntegerField(
        default=24,
        verbose_name=_('Appointment reminder hours (hours before)')
    )
    
    medication_reminder_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Medication reminders enabled')
    )
    
    medication_reminder_times = models.JSONField(
        default=list,
        verbose_name=_('Medication reminder times'),
        help_text=_('In format: ["08:00", "12:00", "18:00"]')
    )
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"{self.user} - Notification Preferences"


class NotificationTemplate(models.Model):
    """
    Notification templates
    """
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        unique=True,
        verbose_name=_('Notification Type')
    )
    
    title_template = models.CharField(
        max_length=200,
        verbose_name=_('Title Template'),
        help_text=_('You can use Django template syntax: {{ variable }}')
    )
    
    message_template = models.TextField(
        verbose_name=_('Message Template'),
        help_text=_('You can use Django template syntax')
    )
    
    email_template = models.TextField(
        blank=True,
        verbose_name=_('Email Template (HTML)'),
        help_text=_('Custom HTML template for email')
    )
    
    sms_template = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_('SMS Template'),
        help_text=_('Short text for SMS (max 160 characters)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
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
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
    
    def __str__(self):
        return f"{self.get_notification_type_display()} Template"


class NotificationLog(models.Model):
    """
    Logs of sent notifications
    """
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Notification')
    )
    
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('web', _('Web')),
            ('email', _('Email')),
            ('sms', _('SMS')),
            ('push', _('Push'))
        ],
        verbose_name=_('Delivery Method')
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('sent', _('Sent')),
            ('delivered', _('Delivered')),
            ('failed', _('Failed')),
            ('bounced', _('Bounced'))
        ],
        default='pending',
        verbose_name=_('Status')
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error Message')
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent At')
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Delivered At')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Notification Log')
        verbose_name_plural = _('Notification Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.get_delivery_method_display()} - {self.get_status_display()}"
