from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from treatments.models import Treatment

class LabTest(models.Model):
    """
    Laboratory test model. Represents tests requested by doctors.
    """
    TEST_STATUS_CHOICES = [
        ('requested', _('Requested')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='lab_tests',
        verbose_name=_('Treatment')
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lab_tests',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_lab_tests',
        verbose_name=_('Requesting Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    test_name = models.CharField(
        max_length=200,
        verbose_name=_('Test Name')
    )
    test_details = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Test Details')
    )
    status = models.CharField(
        max_length=20,
        choices=TEST_STATUS_CHOICES,
        default='requested',
        verbose_name=_('Status')
    )
    requested_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Request Date')
    )
    completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completion Date')
    )
    
    class Meta:
        verbose_name = _('Laboratory Test')
        verbose_name_plural = _('Laboratory Tests')
        ordering = ['-requested_date']
    
    def __str__(self):
        return f"{self.patient} - {self.test_name} - {self.get_status_display()}"

class TestResult(models.Model):
    """
    Test result model. Represents the results of a laboratory test.
    """
    lab_test = models.OneToOneField(
        LabTest,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name=_('Laboratory Test')
    )
    result_text = models.TextField(
        verbose_name=_('Result Text')
    )
    reference_values = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Reference Values')
    )
    is_normal = models.BooleanField(
        default=True,
        verbose_name=_('Is Normal?')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes')
    )
    technician = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Technician/Lab Assistant')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated Date')
    )
    result_file = models.FileField(
        upload_to='lab_results/',
        blank=True,
        null=True,
        verbose_name=_('Result File')
    )
    
    class Meta:
        verbose_name = _('Test Result')
        verbose_name_plural = _('Test Results')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lab_test.test_name} - {self.lab_test.patient}"
    
    def save(self, *args, **kwargs):
        # When test result is added, lab test status is updated to "completed"
        if not self.pk:  # If new record
            self.lab_test.status = 'completed'
            self.lab_test.completed_date = self.created_at
            self.lab_test.save()
        super().save(*args, **kwargs)
