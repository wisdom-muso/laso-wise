"""
Comprehensive Hypertension Management System
Handles hypertensive patient identification, monitoring, alerts, and workflows
"""
import logging
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from treatments.models_vitals import VitalSign, VitalSignAlert
from treatments.models_medical_history import MedicalHistory
from core.models_notifications import Notification

User = get_user_model()
logger = logging.getLogger(__name__)


class HypertensionProfile(models.Model):
    """
    Hypertension-specific patient profile
    """
    HYPERTENSION_STAGES = [
        ('normal', 'Normal (<120/80)'),
        ('elevated', 'Elevated (120-129/<80)'),
        ('stage1', 'Stage 1 (130-139/80-89)'),
        ('stage2', 'Stage 2 (≥140/≥90)'),
        ('crisis', 'Hypertensive Crisis (>180/>120)'),
    ]
    
    RISK_CATEGORIES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk'),
    ]
    
    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='hypertension_profile',
        limit_choices_to={'user_type': 'patient'}
    )
    
    # Hypertension Classification
    current_stage = models.CharField(
        max_length=20,
        choices=HYPERTENSION_STAGES,
        default='normal'
    )
    
    diagnosis_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when hypertension was first diagnosed'
    )
    
    # Risk Assessment
    cardiovascular_risk = models.CharField(
        max_length=20,
        choices=RISK_CATEGORIES,
        default='low'
    )
    
    target_systolic = models.PositiveIntegerField(
        default=130,
        help_text='Target systolic BP for this patient'
    )
    
    target_diastolic = models.PositiveIntegerField(
        default=80,
        help_text='Target diastolic BP for this patient'
    )
    
    # Monitoring Settings
    monitoring_frequency_days = models.PositiveIntegerField(
        default=7,
        help_text='How often BP should be monitored (in days)'
    )
    
    alert_threshold_systolic = models.PositiveIntegerField(
        default=140,
        help_text='Systolic BP threshold for alerts'
    )
    
    alert_threshold_diastolic = models.PositiveIntegerField(
        default=90,
        help_text='Diastolic BP threshold for alerts'
    )
    
    # Treatment Information
    is_on_medication = models.BooleanField(default=False)
    medication_adherence_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Medication adherence score (0-10)'
    )
    
    # Lifestyle Factors
    lifestyle_modifications = models.JSONField(
        default=dict,
        help_text='Lifestyle modification recommendations and progress'
    )
    
    # Flags
    requires_immediate_attention = models.BooleanField(default=False)
    is_controlled = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Hypertension Profile'
        verbose_name_plural = 'Hypertension Profiles'
    
    def __str__(self):
        return f"{self.patient} - {self.get_current_stage_display()}"
    
    def update_stage_from_vitals(self, vital_sign):
        """Update hypertension stage based on latest vital signs"""
        self.current_stage = vital_sign.bp_category
        self.is_controlled = self.current_stage in ['normal', 'elevated']
        self.requires_immediate_attention = self.current_stage in ['stage2', 'crisis']
        self.last_assessment_date = timezone.now()
        self.save()
    
    def get_next_monitoring_date(self):
        """Calculate next monitoring date"""
        if self.last_assessment_date:
            return self.last_assessment_date.date() + timedelta(days=self.monitoring_frequency_days)
        return timezone.now().date()
    
    def is_overdue_for_monitoring(self):
        """Check if patient is overdue for BP monitoring"""
        next_date = self.get_next_monitoring_date()
        return timezone.now().date() > next_date


class HypertensionAlert(models.Model):
    """
    Hypertension-specific alerts and notifications
    """
    ALERT_TYPES = [
        ('high_bp', 'High Blood Pressure Reading'),
        ('crisis_bp', 'Hypertensive Crisis'),
        ('medication_reminder', 'Medication Reminder'),
        ('monitoring_overdue', 'Monitoring Overdue'),
        ('target_not_met', 'Target BP Not Met'),
        ('lifestyle_reminder', 'Lifestyle Modification Reminder'),
        ('follow_up_needed', 'Follow-up Appointment Needed'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hypertension_alerts',
        limit_choices_to={'user_type': 'patient'}
    )
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related data
    vital_sign = models.ForeignKey(
        VitalSign,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='hypertension_alerts'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_hypertension_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications sent
    patient_notified = models.BooleanField(default=False)
    doctor_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Hypertension Alert'
        verbose_name_plural = 'Hypertension Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.get_alert_type_display()}"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.is_active = False
        self.save()


class HypertensionManager:
    """
    Central manager for hypertension-related operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_vital_signs(self, vital_sign):
        """
        Process new vital signs for hypertension management
        """
        patient = vital_sign.patient
        
        # Get or create hypertension profile
        profile, created = HypertensionProfile.objects.get_or_create(
            patient=patient,
            defaults={
                'diagnosis_date': timezone.now().date() if self.is_hypertensive(vital_sign) else None
            }
        )
        
        # Update profile based on new vitals
        profile.update_stage_from_vitals(vital_sign)
        
        # Check for alerts
        self.check_and_create_alerts(vital_sign, profile)
        
        # Update medical history if newly diagnosed
        if created and self.is_hypertensive(vital_sign):
            self.create_hypertension_medical_history(patient)
        
        return profile
    
    def is_hypertensive(self, vital_sign):
        """
        Determine if vital signs indicate hypertension
        """
        return vital_sign.bp_category in ['stage1', 'stage2', 'crisis']
    
    def check_and_create_alerts(self, vital_sign, profile):
        """
        Check vital signs and create appropriate alerts
        """
        alerts_created = []
        
        # High BP Alert
        if (vital_sign.systolic_bp >= profile.alert_threshold_systolic or 
            vital_sign.diastolic_bp >= profile.alert_threshold_diastolic):
            
            priority = 'critical' if vital_sign.bp_category == 'crisis' else 'high'
            alert_type = 'crisis_bp' if vital_sign.bp_category == 'crisis' else 'high_bp'
            
            alert = self.create_alert(
                patient=vital_sign.patient,
                alert_type=alert_type,
                priority=priority,
                title=f"High Blood Pressure Alert: {vital_sign.blood_pressure_display}",
                message=self.get_bp_alert_message(vital_sign),
                vital_sign=vital_sign
            )
            alerts_created.append(alert)
        
        # Target not met alert
        if (vital_sign.systolic_bp > profile.target_systolic or 
            vital_sign.diastolic_bp > profile.target_diastolic):
            
            alert = self.create_alert(
                patient=vital_sign.patient,
                alert_type='target_not_met',
                priority='medium',
                title="Blood Pressure Target Not Met",
                message=f"Current BP: {vital_sign.blood_pressure_display}, Target: {profile.target_systolic}/{profile.target_diastolic}",
                vital_sign=vital_sign
            )
            alerts_created.append(alert)
        
        # Send notifications for critical alerts
        for alert in alerts_created:
            if alert.priority == 'critical':
                self.send_critical_alert_notifications(alert)
        
        return alerts_created
    
    def create_alert(self, patient, alert_type, priority, title, message, vital_sign=None):
        """
        Create a hypertension alert
        """
        alert = HypertensionAlert.objects.create(
            patient=patient,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            vital_sign=vital_sign
        )
        
        self.logger.info(f"Created hypertension alert: {alert}")
        return alert
    
    def get_bp_alert_message(self, vital_sign):
        """
        Generate appropriate message for BP alert
        """
        bp_category = vital_sign.bp_category
        bp_reading = vital_sign.blood_pressure_display
        
        messages = {
            'crisis': f"CRITICAL: Hypertensive crisis detected (BP: {bp_reading}). Immediate medical attention required.",
            'stage2': f"HIGH: Stage 2 hypertension detected (BP: {bp_reading}). Please contact your healthcare provider.",
            'stage1': f"ELEVATED: Stage 1 hypertension detected (BP: {bp_reading}). Monitor closely and consider lifestyle modifications.",
        }
        
        return messages.get(bp_category, f"Blood pressure reading: {bp_reading}")
    
    def create_hypertension_medical_history(self, patient):
        """
        Create medical history entry for newly diagnosed hypertension
        """
        MedicalHistory.objects.create(
            patient=patient,
            condition_type='chronic',
            condition_name='Essential Hypertension',
            diagnosed_date=timezone.now().date(),
            is_active=True,
            notes='Diagnosed based on elevated blood pressure readings'
        )
    
    def send_critical_alert_notifications(self, alert):
        """
        Send notifications for critical hypertension alerts
        """
        try:
            # Notify patient
            self.notify_patient(alert)
            
            # Notify assigned doctors
            self.notify_doctors(alert)
            
            # Update notification flags
            alert.patient_notified = True
            alert.doctor_notified = True
            alert.save()
            
        except Exception as e:
            self.logger.error(f"Failed to send critical alert notifications: {e}")
    
    def notify_patient(self, alert):
        """
        Send notification to patient
        """
        # Create in-app notification
        Notification.objects.create(
            user=alert.patient,
            title=alert.title,
            message=alert.message,
            notification_type='health_alert',
            priority='high' if alert.priority == 'critical' else 'medium'
        )
        
        # Send email if configured
        if hasattr(settings, 'EMAIL_BACKEND') and alert.patient.email:
            try:
                send_mail(
                    subject=f"Health Alert: {alert.title}",
                    message=alert.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[alert.patient.email],
                    fail_silently=False
                )
            except Exception as e:
                self.logger.error(f"Failed to send email to patient: {e}")
    
    def notify_doctors(self, alert):
        """
        Send notification to relevant doctors
        """
        # Find doctors who have treated this patient
        from appointments.models import Appointment
        
        doctors = User.objects.filter(
            user_type='doctor',
            doctor_appointments__patient=alert.patient
        ).distinct()
        
        for doctor in doctors:
            Notification.objects.create(
                user=doctor,
                title=f"Patient Alert: {alert.patient.get_full_name()}",
                message=f"Critical hypertension alert for patient {alert.patient.get_full_name()}: {alert.message}",
                notification_type='patient_alert',
                priority='high'
            )
    
    def check_overdue_monitoring(self):
        """
        Check for patients overdue for BP monitoring
        """
        overdue_profiles = HypertensionProfile.objects.filter(
            last_assessment_date__lt=timezone.now() - timedelta(days=7)
        )
        
        for profile in overdue_profiles:
            if profile.is_overdue_for_monitoring():
                self.create_alert(
                    patient=profile.patient,
                    alert_type='monitoring_overdue',
                    priority='medium',
                    title="Blood Pressure Monitoring Overdue",
                    message=f"Your blood pressure monitoring is overdue. Last check: {profile.last_assessment_date.strftime('%Y-%m-%d') if profile.last_assessment_date else 'Never'}"
                )
    
    def generate_hypertension_report(self, patient, days=30):
        """
        Generate comprehensive hypertension report for a patient
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get vital signs in date range
        vitals = VitalSign.objects.filter(
            patient=patient,
            recorded_at__range=[start_date, end_date]
        ).order_by('-recorded_at')
        
        # Get hypertension profile
        try:
            profile = HypertensionProfile.objects.get(patient=patient)
        except HypertensionProfile.DoesNotExist:
            profile = None
        
        # Calculate statistics
        if vitals.exists():
            avg_systolic = sum(v.systolic_bp for v in vitals) / len(vitals)
            avg_diastolic = sum(v.diastolic_bp for v in vitals) / len(vitals)
            max_systolic = max(v.systolic_bp for v in vitals)
            max_diastolic = max(v.diastolic_bp for v in vitals)
            
            # Count readings by category
            bp_categories = {}
            for vital in vitals:
                category = vital.bp_category
                bp_categories[category] = bp_categories.get(category, 0) + 1
        else:
            avg_systolic = avg_diastolic = max_systolic = max_diastolic = 0
            bp_categories = {}
        
        # Get recent alerts
        alerts = HypertensionAlert.objects.filter(
            patient=patient,
            created_at__range=[start_date, end_date]
        ).order_by('-created_at')
        
        report = {
            'patient': patient,
            'profile': profile,
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'total_readings': vitals.count(),
            'statistics': {
                'avg_systolic': round(avg_systolic, 1),
                'avg_diastolic': round(avg_diastolic, 1),
                'max_systolic': max_systolic,
                'max_diastolic': max_diastolic,
            },
            'bp_categories': bp_categories,
            'recent_vitals': list(vitals[:10]),
            'alerts': list(alerts),
            'is_controlled': profile.is_controlled if profile else False,
            'recommendations': self.get_recommendations(patient, vitals, profile)
        }
        
        return report
    
    def get_recommendations(self, patient, vitals, profile):
        """
        Generate personalized recommendations
        """
        recommendations = []
        
        if not vitals.exists():
            recommendations.append("Regular blood pressure monitoring is recommended")
            return recommendations
        
        latest_vital = vitals.first()
        
        # BP-based recommendations
        if latest_vital.bp_category == 'crisis':
            recommendations.append("URGENT: Seek immediate medical attention")
        elif latest_vital.bp_category == 'stage2':
            recommendations.append("Schedule appointment with healthcare provider within 1 week")
        elif latest_vital.bp_category == 'stage1':
            recommendations.append("Consider lifestyle modifications and medication review")
        
        # Lifestyle recommendations
        if latest_vital.bmi and latest_vital.bmi > 25:
            recommendations.append("Weight management through diet and exercise")
        
        recommendations.extend([
            "Reduce sodium intake to less than 2300mg per day",
            "Engage in regular physical activity (150 minutes/week)",
            "Limit alcohol consumption",
            "Manage stress through relaxation techniques",
            "Ensure adequate sleep (7-9 hours per night)"
        ])
        
        return recommendations


# Utility functions for hypertension management
def identify_hypertensive_patients():
    """
    Identify patients with hypertension based on recent vital signs
    """
    recent_date = timezone.now() - timedelta(days=90)
    
    # Find patients with recent high BP readings
    high_bp_vitals = VitalSign.objects.filter(
        recorded_at__gte=recent_date,
        systolic_bp__gte=130
    ).values('patient').distinct()
    
    hypertensive_patients = []
    
    for vital_data in high_bp_vitals:
        patient = User.objects.get(id=vital_data['patient'])
        
        # Check if they have multiple high readings
        high_readings = VitalSign.objects.filter(
            patient=patient,
            recorded_at__gte=recent_date,
            systolic_bp__gte=130
        ).count()
        
        if high_readings >= 2:  # At least 2 high readings
            hypertensive_patients.append(patient)
    
    return hypertensive_patients


def create_hypertension_workflow(patient):
    """
    Create automated workflow for hypertensive patient
    """
    manager = HypertensionManager()
    
    # Create or update hypertension profile
    profile, created = HypertensionProfile.objects.get_or_create(
        patient=patient,
        defaults={
            'diagnosis_date': timezone.now().date(),
            'monitoring_frequency_days': 7,  # Weekly monitoring
            'alert_threshold_systolic': 140,
            'alert_threshold_diastolic': 90,
        }
    )
    
    # Create medical history entry
    if created:
        manager.create_hypertension_medical_history(patient)
    
    # Schedule follow-up reminders
    manager.create_alert(
        patient=patient,
        alert_type='follow_up_needed',
        priority='medium',
        title="Hypertension Follow-up Required",
        message="Please schedule a follow-up appointment to discuss your blood pressure management plan."
    )
    
    return profile