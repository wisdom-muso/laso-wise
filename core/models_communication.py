from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class CommunicationNotification(models.Model):
    """
    Notification model. Represents notifications sent to users within the system.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('appointment', _('Appointment Notification')),
        ('test_result', _('Test Result Notification')),
        ('prescription', _('Prescription Notification')),
        ('message', _('Message Notification')),
        ('system', _('System Notification')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_notifications',
        verbose_name=_('User')
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name=_('Notification Type')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title')
    )
    message = models.TextField(
        verbose_name=_('Message')
    )
    related_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Related URL')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read?')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    
    class Meta:
        verbose_name = _('Communication Notification')
        verbose_name_plural = _('Communication Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.title}"
    
    def mark_as_read(self):
        """
        Marks the notification as read
        """
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

class Message(models.Model):
    """
    Message model. Represents messaging between users.
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Sender')
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_('Receiver')
    )
    subject = models.CharField(
        max_length=200,
        verbose_name=_('Subject')
    )
    content = models.TextField(
        verbose_name=_('Content')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read?')
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Parent Message')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.subject}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

class EmailTemplate(models.Model):
    """
    Email template model. Represents templates for emails sent by the system.
    """
    TEMPLATE_TYPE_CHOICES = [
        ('appointment_reminder', _('Appointment Reminder')),
        ('appointment_confirmation', _('Appointment Confirmation')),
        ('appointment_cancellation', _('Appointment Cancellation')),
        ('test_result', _('Test Result Notification')),
        ('prescription', _('Prescription Notification')),
        ('welcome', _('Welcome')),
        ('password_reset', _('Password Reset')),
        ('custom', _('Custom Template')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Template Name')
    )
    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPE_CHOICES,
        verbose_name=_('Template Type')
    )
    subject = models.CharField(
        max_length=200,
        verbose_name=_('Email Subject')
    )
    content = models.TextField(
        verbose_name=_('Email Content'),
        help_text=_('You can use HTML. Use {{variable_name}} format for variables.')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated Date')
    )
    
    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
