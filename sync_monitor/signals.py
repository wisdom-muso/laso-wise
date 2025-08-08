from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import mail_admins

from .models import SyncStatus, SystemHealthCheck


@receiver(post_save, sender=SyncStatus)
def notify_on_sync_failure(sender, instance, created, **kwargs):
    """
    Send notification to admins when a sync operation fails
    """
    if not created and instance.status == 'failed':
        subject = f"ALERT: Sync Operation Failed - {instance.get_sync_type_display()}"
        message = f"""
        A synchronization operation has failed:
        
        Type: {instance.get_sync_type_display()}
        Started: {instance.started_at}
        Completed: {instance.completed_at}
        Records Processed: {instance.records_processed}
        Records Failed: {instance.records_failed}
        
        Error Message:
        {instance.error_message}
        
        Please check the system dashboard for more details.
        """
        mail_admins(subject, message, fail_silently=True)


@receiver(post_save, sender=SystemHealthCheck)
def notify_on_critical_health_status(sender, instance, created, **kwargs):
    """
    Send notification to admins when system health becomes critical
    """
    if instance.status == 'critical':
        subject = f"CRITICAL ALERT: System Health Issue - {instance.get_check_type_display()}"
        message = f"""
        A critical system health issue has been detected:
        
        Component: {instance.get_check_type_display()}
        Status: {instance.get_status_display()}
        Time: {instance.checked_at}
        Response Time: {instance.response_time} ms
        
        Details:
        {instance.details}
        
        Please investigate immediately.
        """
        mail_admins(subject, message, fail_silently=True)