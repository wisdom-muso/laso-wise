from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from treatments.models import Treatment

class MedicalImage(models.Model):
    """
    Medical image model. Represents images like X-ray, MRI, CT scans.
    """
    IMAGE_TYPE_CHOICES = [
        ('xray', _('X-ray')),
        ('mri', _('MRI')),
        ('ct', _('CT (Computed Tomography)')),
        ('ultrasound', _('Ultrasound')),
        ('other', _('Other')),
    ]
    
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='medical_images',
        verbose_name=_('Treatment')
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_images',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordered_medical_images',
        verbose_name=_('Requesting Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        verbose_name=_('Image Type')
    )
    body_part = models.CharField(
        max_length=100,
        verbose_name=_('Body Region')
    )
    image_file = models.ImageField(
        upload_to='medical_images/',
        verbose_name=_('Image File')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    taken_date = models.DateField(
        verbose_name=_('Date Taken')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation Date')
    )
    
    class Meta:
        verbose_name = _('Medical Image')
        verbose_name_plural = _('Medical Images')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.get_image_type_display()} - {self.body_part}"

class Report(models.Model):
    """
    Report model. Represents reports created by doctors.
    """
    REPORT_TYPE_CHOICES = [
        ('diagnostic', _('Diagnostic Report')),
        ('progress', _('Progress Report')),
        ('discharge', _('Discharge Report')),
        ('consultation', _('Consultation Report')),
        ('sick_leave', _('Sick Leave Report')),
        ('other', _('Other')),
    ]
    
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Treatment')
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='written_reports',
        verbose_name=_('Reporting Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_('Report Type')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Report Title')
    )
    content = models.TextField(
        verbose_name=_('Report Content')
    )
    valid_from = models.DateField(
        verbose_name=_('Valid From')
    )
    valid_until = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Valid Until')
    )
    report_file = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True,
        verbose_name=_('Report File')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation Date')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Update Date')
    )
    
    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.title} - {self.valid_from}"
