from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import json

class SystemStatistics(models.Model):
    """
    System statistics model. Stores system statistics for a specific time period.
    """
    date = models.DateField(
        unique=True,
        verbose_name=_('Date')
    )
    total_patients = models.IntegerField(
        default=0,
        verbose_name=_('Total Patients')
    )
    total_doctors = models.IntegerField(
        default=0,
        verbose_name=_('Total Doctors')
    )
    total_appointments = models.IntegerField(
        default=0,
        verbose_name=_('Total Appointments')
    )
    completed_appointments = models.IntegerField(
        default=0,
        verbose_name=_('Completed Appointments')
    )
    cancelled_appointments = models.IntegerField(
        default=0,
        verbose_name=_('Cancelled Appointments')
    )
    total_treatments = models.IntegerField(
        default=0,
        verbose_name=_('Total Treatments')
    )
    daily_active_users = models.IntegerField(
        default=0,
        verbose_name=_('Daily Active Users')
    )
    data_json = models.JSONField(
        default=dict,
        verbose_name=_('Extra Data (JSON)'),
        help_text=_('You can store extra statistical data in JSON format in this field.')
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
        verbose_name = _('System Statistic')
        verbose_name_plural = _('System Statistics')
        ordering = ['-date']
    
    def __str__(self):
        return f"Statistics: {self.date}"
    
    def get_data_as_dict(self):
        if isinstance(self.data_json, str):
            return json.loads(self.data_json)
        return self.data_json

class DoctorStatistics(models.Model):
    """
    Doctor statistics model. Stores doctor statistics for a specific time period.
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statistics',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    date = models.DateField(
        verbose_name=_('Date')
    )
    appointment_count = models.IntegerField(
        default=0,
        verbose_name=_('Appointment Count')
    )
    completed_appointment_count = models.IntegerField(
        default=0,
        verbose_name=_('Completed Appointment Count')
    )
    treatment_count = models.IntegerField(
        default=0,
        verbose_name=_('Treatment Count')
    )
    prescription_count = models.IntegerField(
        default=0,
        verbose_name=_('Prescription Count')
    )
    lab_test_count = models.IntegerField(
        default=0,
        verbose_name=_('Lab Test Count')
    )
    average_appointment_duration = models.FloatField(
        default=0.0,
        verbose_name=_('Average Appointment Duration (minutes)')
    )
    data_json = models.JSONField(
        default=dict,
        verbose_name=_('Extra Data (JSON)')
    )
    
    class Meta:
        verbose_name = _('Doctor Statistic')
        verbose_name_plural = _('Doctor Statistics')
        ordering = ['-date']
        unique_together = ['doctor', 'date']
    
    def __str__(self):
        return f"{self.doctor} - {self.date}"

class DoctorPerformanceMetric(models.Model):
    """
    Doctor performance metric model. Stores doctor performance evaluations.
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_metrics',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    date = models.DateField(
        verbose_name=_('Date')
    )
    appointments_count = models.IntegerField(
        default=0,
        verbose_name=_('Appointments Count')
    )
    treatments_count = models.IntegerField(
        default=0,
        verbose_name=_('Treatments Count')
    )
    average_rating = models.FloatField(
        default=0.0,
        verbose_name=_('Average Rating (out of 5)')
    )
    patient_satisfaction = models.FloatField(
        default=0.0,
        verbose_name=_('Patient Satisfaction (out of 100)')
    )
    efficiency_score = models.FloatField(
        default=0.0,
        verbose_name=_('Efficiency Score (out of 100)')
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
        verbose_name = _('Doctor Performance Metric')
        verbose_name_plural = _('Doctor Performance Metrics')
        ordering = ['-date']
        unique_together = ['doctor', 'date']
    
    def __str__(self):
        return f"{self.doctor} - {self.date}"

class ReportTemplate(models.Model):
    """
    Report template model. Used to create custom reports.
    """
    REPORT_TYPE_CHOICES = [
        ('doctor_performance', _('Doctor Performance Report')),
        ('patient_statistics', _('Patient Statistics Report')),
        ('financial', _('Financial Report')),
        ('appointment', _('Appointment Report')),
        ('treatment', _('Treatment Report')),
        ('custom', _('Custom Report')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Template Name')
    )
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_('Report Type')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    query = models.TextField(
        verbose_name=_('SQL Query'),
        help_text=_('SQL query to be executed when generating a report using this template.')
    )
    columns = models.JSONField(
        default=list,
        verbose_name=_('Columns'),
        help_text=_('Columns to be displayed in the report. JSON format: [{"name": "column_name", "display": "Display Name"}]')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
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
        verbose_name = _('Report Template')
        verbose_name_plural = _('Report Templates')
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    """
    Generated report model. Represents reports generated using ReportTemplate.
    """
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name=_('Report Template')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Report Name')
    )
    parameters = models.JSONField(
        default=dict,
        verbose_name=_('Parameters'),
        help_text=_('Parameters used when generating the report. In JSON format.')
    )
    result_data = models.JSONField(
        default=list,
        verbose_name=_('Result Data'),
        help_text=_('Report result. In JSON format.')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_('Creator')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation Date')
    )
    report_file = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True,
        verbose_name=_('Report File')
    )
    
    class Meta:
        verbose_name = _('Generated Report')
        verbose_name_plural = _('Generated Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"


