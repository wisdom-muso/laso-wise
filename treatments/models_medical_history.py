from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class MedicalHistory(models.Model):
    """
    Patient medical history model. Contains information about chronic diseases, 
    past surgeries, allergies, etc.
    """
    CONDITION_TYPE_CHOICES = [
        ('chronic', _('Chronic Disease')),
        ('surgery', _('Past Surgery')),
        ('allergy', _('Allergy')),
        ('medication', _('Regular Medication Use')),
        ('other', _('Other')),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_history',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    condition_type = models.CharField(
        max_length=20,
        choices=CONDITION_TYPE_CHOICES,
        verbose_name=_('Condition Type')
    )
    condition_name = models.CharField(
        max_length=200,
        verbose_name=_('Condition Name/Description')
    )
    diagnosed_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Diagnosis Date')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Additional Notes')
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
        verbose_name = _('Medical History Record')
        verbose_name_plural = _('Medical History Records')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.get_condition_type_display()}: {self.condition_name}"
