from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model
    Each user can be a patient, doctor, receptionist, or admin.
    """
    USER_TYPE_CHOICES = [
        ('patient', _('Patient')),
        ('doctor', _('Doctor')),
        ('receptionist', _('Receptionist')),
        ('admin', _('Admin')),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='patient',
        verbose_name='User Type'
    )
    
    # Doktorlar için ek alanlar
    specialization = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Specialization'
    )
    
    # Hastalar için ek alanlar
    date_of_birth = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Date of Birth'
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Phone Number'
    )
    address = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Address'
    )
    blood_type = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name='Blood Type'
    )
    
    def is_patient(self):
        return self.user_type == 'patient'
    
    def is_doctor(self):
        return self.user_type == 'doctor'
    
    def is_receptionist(self):
        return self.user_type == 'receptionist'
    
    def is_admin_user(self):
        return self.user_type == 'admin'
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
