from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Medication(models.Model):
    """
    Medication database. Contains information about all medications.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_('Medication Name')
    )
    active_ingredient = models.CharField(
        max_length=200,
        verbose_name=_('Active Ingredient')
    )
    drug_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Drug Code')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    side_effects = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Side Effects')
    )
    contraindications = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Contraindications')
    )
    is_prescription = models.BooleanField(
        default=True,
        verbose_name=_('Prescription Required?')
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
        verbose_name = _('Medication')
        verbose_name_plural = _('Medications')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.active_ingredient})"

class MedicationInteraction(models.Model):
    """
    Medication interactions. Defines possible interactions between two medications.
    """
    SEVERITY_CHOICES = [
        ('mild', _('Mild')),
        ('moderate', _('Moderate')),
        ('severe', _('Severe')),
    ]
    
    medication1 = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='interactions_as_first',
        verbose_name=_('Medication 1')
    )
    medication2 = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='interactions_as_second',
        verbose_name=_('Medication 2')
    )
    description = models.TextField(
        verbose_name=_('Interaction Description')
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        verbose_name=_('Severity')
    )
    recommendations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Recommendations')
    )
    
    class Meta:
        verbose_name = _('Medication Interaction')
        verbose_name_plural = _('Medication Interactions')
        unique_together = [['medication1', 'medication2']]
        
    def __str__(self):
        return f"{self.medication1.name} - {self.medication2.name} ({self.get_severity_display()})"

# treatments/models.py dosyasında bulunan Prescription modeline eklenecek alanlar:
# from treatments.models_medications import Medication

# class Prescription(models.Model):
#     ...
#     medication = models.ForeignKey(
#         Medication,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='prescriptions',
#         verbose_name=_('İlaç')
#     )
#     ...
