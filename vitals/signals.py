from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import VitalRecord, VitalNotification, VitalGoal

User = get_user_model()


@receiver(post_save, sender=VitalRecord)
def create_vital_notification(sender, instance, created, **kwargs):
    """
    Create notifications for abnormal vital signs
    """
    if created:
        # Check if vital sign is abnormal or critical
        if instance.status in ['abnormal-low', 'abnormal-high', 'critical-low', 'critical-high']:
            # Create notification for the patient
            message = f"Your {instance.category.name} reading of {instance.value} {instance.category.unit} is {instance.status_display}. "
            
            if instance.status.startswith('critical'):
                message += "Please consult a healthcare provider immediately."
                severity = 'danger'
            else:
                message += "Please monitor your condition and consider consulting a healthcare provider."
                severity = 'warning'
            
            VitalNotification.objects.create(
                patient=instance.patient,
                vital_record=instance,
                message=message,
                severity=severity
            )
            
            # If this was recorded by a healthcare professional, also notify them
            if instance.recorded_by and instance.recorded_by.role in ['doctor', 'admin']:
                VitalNotification.objects.create(
                    patient=instance.recorded_by,  # Notify the doctor/admin
                    vital_record=instance,
                    message=f"Patient {instance.patient.get_full_name()} has {instance.status_display} {instance.category.name}: {instance.value} {instance.category.unit}",
                    severity=severity
                )


@receiver(post_save, sender=VitalGoal)
def create_goal_notification(sender, instance, created, **kwargs):
    """
    Create notifications for goal achievements
    """
    if created:
        # Notify patient about new goal
        message = f"A new health goal has been set for {instance.category.name}: {instance.target_value} {instance.category.unit}"
        if instance.target_date:
            message += f" (Target date: {instance.target_date.strftime('%B %d, %Y')})"
        
        VitalNotification.objects.create(
            patient=instance.patient,
            vital_record=None,
            message=message,
            severity='info'
        )
    
    elif instance.is_achieved and not instance.achieved_date:
        # Goal was just achieved
        instance.achieved_date = timezone.now().date()
        instance.save()
        
        # Create achievement notification
        message = f"Congratulations! You've achieved your {instance.category.name} goal of {instance.target_value} {instance.category.unit}!"
        
        VitalNotification.objects.create(
            patient=instance.patient,
            vital_record=None,
            message=message,
            severity='info'
        )


@receiver(post_save, sender=VitalRecord)
def check_goal_achievement(sender, instance, created, **kwargs):
    """
    Check if a vital record achieves any active goals
    """
    if created:
        # Get active goals for this patient and category
        active_goals = VitalGoal.objects.filter(
            patient=instance.patient,
            category=instance.category,
            is_achieved=False
        )
        
        for goal in active_goals:
            # Check if the goal is achieved (within 5% tolerance)
            tolerance = goal.target_value * 0.05
            if abs(instance.value - goal.target_value) <= tolerance:
                goal.is_achieved = True
                goal.achieved_date = timezone.now().date()
                goal.save()
                
                # Create achievement notification
                message = f"Goal achieved! Your {instance.category.name} reading of {instance.value} {instance.category.unit} meets your target of {goal.target_value} {instance.category.unit}."
                
                VitalNotification.objects.create(
                    patient=instance.patient,
                    vital_record=instance,
                    message=message,
                    severity='info'
                )


@receiver(post_save, sender=VitalRecord)
def check_trend_alerts(sender, instance, created, **kwargs):
    """
    Check for concerning trends in vital signs
    """
    if created:
        # Get recent vital records for this patient and category (last 5 readings)
        recent_records = VitalRecord.objects.filter(
            patient=instance.patient,
            category=instance.category
        ).order_by('-recorded_at')[:5]
        
        if recent_records.count() >= 3:
            # Check if there's a concerning trend
            values = [record.value for record in recent_records]
            
            # Check for consistently increasing or decreasing values
            if len(values) >= 3:
                # Calculate trend
                trend = 0
                for i in range(1, len(values)):
                    if values[i] > values[i-1]:
                        trend += 1
                    elif values[i] < values[i-1]:
                        trend -= 1
                
                # If trend is consistently in one direction and values are outside normal range
                if abs(trend) >= 2:  # At least 2 out of 3 readings show same trend
                    latest_value = values[0]
                    
                    # Check if latest value is outside normal range
                    if (instance.category.min_normal and latest_value < instance.category.min_normal) or \
                       (instance.category.max_normal and latest_value > instance.category.max_normal):
                        
                        trend_direction = "increasing" if trend > 0 else "decreasing"
                        message = f"Concerning trend detected: Your {instance.category.name} is {trend_direction} and currently outside normal range ({latest_value} {instance.category.unit}). Please consult a healthcare provider."
                        
                        VitalNotification.objects.create(
                            patient=instance.patient,
                            vital_record=instance,
                            message=message,
                            severity='warning'
                        )


@receiver(post_save, sender=VitalRecord)
def check_emergency_alerts(sender, instance, created, **kwargs):
    """
    Check for emergency-level vital signs
    """
    if created and instance.status.startswith('critical'):
        # Create emergency alert
        message = f"EMERGENCY ALERT: {instance.patient.get_full_name()} has critical {instance.category.name}: {instance.value} {instance.category.unit}. Immediate medical attention required."
        
        # Notify all doctors and admins
        healthcare_providers = User.objects.filter(role__in=['doctor', 'admin'])
        
        for provider in healthcare_providers:
            VitalNotification.objects.create(
                patient=provider,  # Notify the healthcare provider
                vital_record=instance,
                message=message,
                severity='danger'
            )


@receiver(post_save, sender=VitalRecord)
def update_health_score(sender, instance, created, **kwargs):
    """
    Update patient's health score based on vital signs
    """
    if created:
        # This could be expanded to calculate a comprehensive health score
        # For now, we'll just track the notification
        pass