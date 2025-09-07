from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from appointments.models import Appointment

class Treatment(models.Model):
    """
    Treatment model, contains treatment information applied by doctor to patient as a result of an appointment.
    """
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='treatment',
        verbose_name=_('Appointment')
    )
    diagnosis = models.TextField(
        verbose_name=_('Diagnosis')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes')
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
        verbose_name = _('Treatment')
        verbose_name_plural = _('Treatments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.appointment.patient} - {self.diagnosis[:30]}"

class Prescription(models.Model):
    """
    Prescription model, contains medication information given for a treatment.
    """
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Treatment')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Medication Name')
    )
    medication = models.ForeignKey(
        'treatments.Medication',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions',
        verbose_name=_('Medication')
    )
    dosage = models.CharField(
        max_length=100,
        verbose_name=_('Dosage')
    )
    instructions = models.TextField(
        verbose_name=_('Usage Instructions')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Prescription')
        verbose_name_plural = _('Prescriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.dosage}"

# Diğer modeller için import
from .models_medical_history import MedicalHistory
from .models_lab import LabTest, TestResult
from .models_medications import Medication, MedicationInteraction
from .models_imaging import MedicalImage, Report
