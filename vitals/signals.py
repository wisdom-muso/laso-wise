from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import VitalRecord, VitalNotification, VitalGoal


@receiver(post_save, sender=VitalRecord)
def create_notification_for_abnormal_vitals(sender, instance, created, **kwargs):
    """
    Create a notification when a vital record is abnormal
    """
    if created and instance.status in ['critical-low', 'critical-high', 'abnormal-low', 'abnormal-high']:
        severity = 'danger' if 'critical' in instance.status else 'warning'
        
        message = _(f"Your {instance.category.name} reading of {instance.value} {instance.category.unit} "
                   f"is {instance.status_display.lower()}. Please consult with your doctor.")
        
        VitalNotification.objects.create(
            patient=instance.patient,
            vital_record=instance,
            message=message,
            severity=severity
        )


@receiver(post_save, sender=VitalRecord)
def check_goal_achievement(sender, instance, created, **kwargs):
    """
    Check if any goals have been achieved with this vital record
    """
    if created:
        # Get active goals for this category
        goals = VitalGoal.objects.filter(
            patient=instance.patient,
            category=instance.category,
            is_achieved=False
        )
        
        for goal in goals:
            # Check if goal is achieved
            if goal.category.name.lower() == 'weight' and instance.value <= goal.target_value:
                goal.is_achieved = True
                goal.achieved_date = instance.recorded_at.date()
                goal.save()
                
                # Create notification
                message = _(f"Congratulations! You've achieved your {goal.category.name} goal of "
                           f"{goal.target_value} {goal.category.unit}.")
                
                VitalNotification.objects.create(
                    patient=instance.patient,
                    vital_record=instance,
                    message=message,
                    severity='info'
                )
            
            # For other vitals like blood pressure, heart rate, etc.
            # The logic may vary depending on the goal (lower or higher)
            elif goal.category.name.lower() in ['blood pressure', 'heart rate', 'cholesterol'] and instance.value <= goal.target_value:
                goal.is_achieved = True
                goal.achieved_date = instance.recorded_at.date()
                goal.save()
                
                # Create notification
                message = _(f"Congratulations! You've achieved your {goal.category.name} goal of "
                           f"{goal.target_value} {goal.category.unit}.")
                
                VitalNotification.objects.create(
                    patient=instance.patient,
                    vital_record=instance,
                    message=message,
                    severity='info'
                )