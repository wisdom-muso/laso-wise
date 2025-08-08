from django.db import models
from django.conf import settings
from django.utils import timezone

class MobileClinicRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mobile_clinic_requests'
    )
    requested_date = models.DateField()
    requested_time = models.TimeField()
    address = models.TextField()
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Mobile Clinic Request by {self.patient.get_full_name()} on {self.requested_date}"
    
    class Meta:
        ordering = ['-created_at']


class MobileClinicNotification(models.Model):
    request = models.ForeignKey(
        MobileClinicRequest, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.request}"
    
    class Meta:
        ordering = ['-created_at']