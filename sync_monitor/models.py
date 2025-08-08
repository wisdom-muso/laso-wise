from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class SyncStatus(models.Model):
    """
    Model to track the status of data synchronization between the platform and external systems
    """
    SYNC_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )

    SYNC_TYPE_CHOICES = (
        ('patient_data', _('Patient Data')),
        ('doctor_data', _('Doctor Data')),
        ('appointment_data', _('Appointment Data')),
        ('prescription_data', _('Prescription Data')),
        ('vital_data', _('Vital Signs Data')),
        ('hospital_data', _('Hospital Data')),
        ('full_sync', _('Full System Sync')),
    )

    sync_type = models.CharField(
        max_length=50, 
        choices=SYNC_TYPE_CHOICES,
        verbose_name=_('Sync Type')
    )
    status = models.CharField(
        max_length=20, 
        choices=SYNC_STATUS_CHOICES, 
        default='pending',
        verbose_name=_('Status')
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Started At')
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('Completed At')
    )
    records_processed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Records Processed')
    )
    records_failed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Records Failed')
    )
    error_message = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Error Message')
    )
    initiated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='initiated_syncs',
        verbose_name=_('Initiated By')
    )
    
    class Meta:
        verbose_name = _('Sync Status')
        verbose_name_plural = _('Sync Status')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    def mark_completed(self):
        """Mark the sync as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark the sync as failed with an error message"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()
    
    def duration(self):
        """Calculate the duration of the sync process"""
        if self.completed_at:
            return self.completed_at - self.started_at
        elif self.status == 'in_progress':
            return timezone.now() - self.started_at
        return None
    
    @property
    def success_rate(self):
        """Calculate the success rate of the sync process"""
        if self.records_processed == 0:
            return 0
        return round(((self.records_processed - self.records_failed) / self.records_processed) * 100, 2)


class SystemHealthCheck(models.Model):
    """
    Model to track system health checks
    """
    STATUS_CHOICES = (
        ('healthy', _('Healthy')),
        ('warning', _('Warning')),
        ('critical', _('Critical')),
    )
    
    CHECK_TYPE_CHOICES = (
        ('database', _('Database')),
        ('api', _('API Services')),
        ('storage', _('Storage')),
        ('cache', _('Cache')),
        ('queue', _('Queue')),
        ('overall', _('Overall System')),
    )
    
    check_type = models.CharField(
        max_length=50, 
        choices=CHECK_TYPE_CHOICES,
        verbose_name=_('Check Type')
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='healthy',
        verbose_name=_('Status')
    )
    details = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Details')
    )
    response_time = models.FloatField(
        default=0.0,
        verbose_name=_('Response Time (ms)')
    )
    checked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Checked At')
    )
    
    class Meta:
        verbose_name = _('System Health Check')
        verbose_name_plural = _('System Health Checks')
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"{self.get_check_type_display()} - {self.get_status_display()} ({self.checked_at.strftime('%Y-%m-%d %H:%M')})"


class DataSyncLog(models.Model):
    """
    Model to log individual data sync operations
    """
    sync_status = models.ForeignKey(
        SyncStatus, 
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Sync Status')
    )
    entity_type = models.CharField(
        max_length=100,
        verbose_name=_('Entity Type')
    )
    entity_id = models.CharField(
        max_length=100,
        verbose_name=_('Entity ID')
    )
    action = models.CharField(
        max_length=50,
        verbose_name=_('Action')
    )
    success = models.BooleanField(
        default=True,
        verbose_name=_('Success')
    )
    error_message = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Error Message')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )
    
    class Meta:
        verbose_name = _('Data Sync Log')
        verbose_name_plural = _('Data Sync Logs')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.entity_type} {self.entity_id} - {self.action} - {'Success' if self.success else 'Failed'}"