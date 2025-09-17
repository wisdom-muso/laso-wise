from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from core.models_communication import CommunicationNotification
from appointments.models_availability import DoctorAvailability, DoctorTimeOff
from users.models import User


def create_notification(user, notification_type, title, message, related_url=None):
    """
    Helper function that creates a notification for the user.
    
    Args:
        user: User object (User)
        notification_type: Notification type (one of choices)
        title: Notification title
        message: Notification message
        related_url: Related URL (optional)
    
    Returns:
        The created notification object
    """
    notification = CommunicationNotification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_url=related_url
    )
    
    return notification


def create_availability_change_notification(doctor, operation_type, day=None, start_time=None, end_time=None):
    """
    Function that sends a notification to patients for a doctor's availability change.
    
    Args:
        doctor: Doctor object (User)
        operation_type: Operation type ('added', 'updated', 'deleted')
        day: Day of the change (optional)
        start_time: Start time (optional)
        end_time: End time (optional)
    """
    # Find the doctor's patients (unique patients who have an appointment with the doctor)
    patients = User.objects.filter(
        user_type='patient',
        patient_appointments__doctor=doctor
    ).distinct()
    
    # Create notification title and message based on the operation type
    if operation_type == 'added':
        title = f"Dr. {doctor.get_full_name()} has added new working hours"
        if day is not None and start_time is not None and end_time is not None:
            day_name = DoctorAvailability.WEEKDAY_CHOICES[day][1]
            message = f"Dr. {doctor.get_full_name()} has added new working hours between {start_time} - {end_time} for {day_name}s."
        else:
            message = f"Dr. {doctor.get_full_name()} has updated his working hours. Please check the doctor's calendar to make an appointment."
    
    elif operation_type == 'updated':
        title = f"Dr. {doctor.get_full_name()} has updated his working hours"
        if day is not None and start_time is not None and end_time is not None:
            day_name = DoctorAvailability.WEEKDAY_CHOICES[day][1]
            message = f"Dr. {doctor.get_full_name()} has updated his working hours to {start_time} - {end_time} for {day_name}s."
        else:
            message = f"Dr. {doctor.get_full_name()} has updated his working hours. Please check the doctor's calendar to make an appointment."
    
    elif operation_type == 'deleted':
        title = f"Dr. {doctor.get_full_name()} has removed some working hours"
        if day is not None:
            day_name = DoctorAvailability.WEEKDAY_CHOICES[day][1]
            message = f"Dr. {doctor.get_full_name()} has removed some working hours for {day_name}. Please check the doctor's calendar to make an appointment."
        else:
            message = f"Dr. {doctor.get_full_name()} has made changes to his working hours. Please check the doctor's calendar to make an appointment."
    
    else:  # Add/update/delete time off
        title = f"Change in Dr. {doctor.get_full_name()}'s time off status"
        message = f"There has been a change in Dr. {doctor.get_full_name()}'s time off status. Please check the doctor's calendar to make an appointment."
    
    # Create related URL (doctor calendar)
    related_url = reverse('doctor-calendar', kwargs={'doctor_id': doctor.id})
    
    # Create a notification for each patient
    for patient in patients:
        create_notification(
            user=patient,
            notification_type='system',
            title=title,
            message=message,
            related_url=related_url
        )


# Signal receivers
@receiver(post_save, sender=DoctorAvailability)
def doctor_availability_changed(sender, instance, created, **kwargs):
    """Signal receiver that runs when the DoctorAvailability model changes"""
    if created:
        # When a new working hour is added
        create_availability_change_notification(
            doctor=instance.doctor,
            operation_type='added',
            day=instance.weekday,
            start_time=instance.start_time,
            end_time=instance.end_time
        )
    else:
        # When an existing working hour is updated
        create_availability_change_notification(
            doctor=instance.doctor,
            operation_type='updated', 
            day=instance.weekday,
            start_time=instance.start_time,
            end_time=instance.end_time
        )


@receiver(post_delete, sender=DoctorAvailability)
def doctor_availability_deleted(sender, instance, **kwargs):
    """Signal receiver that runs when the DoctorAvailability model is deleted"""
    create_availability_change_notification(
        doctor=instance.doctor,
        operation_type='deleted',
        day=instance.weekday
    )


@receiver(post_save, sender=DoctorTimeOff)
def doctor_timeoff_changed(sender, instance, created, **kwargs):
    """Signal receiver that runs when the DoctorTimeOff model changes"""
    create_availability_change_notification(
        doctor=instance.doctor,
        operation_type='timeoff'
    )


@receiver(post_delete, sender=DoctorTimeOff)
def doctor_timeoff_deleted(sender, instance, **kwargs):
    """Signal receiver that runs when the DoctorTimeOff model is deleted"""
    create_availability_change_notification(
        doctor=instance.doctor, 
        operation_type='timeoff'
    )


def send_appointment_reminder_email(appointment):
    """
    Sends an appointment reminder email
    """
    subject = f'Laso Healthcare - Appointment Reminder: {appointment.date.strftime("%d.%m.%Y")}'
    
    message = f"""Dear {appointment.patient.get_full_name()},

This email is sent to remind you of your upcoming appointment.

Appointment Information:
Date: {appointment.date.strftime("%d.%m.%Y")}
Time: {appointment.time.strftime("%H:%M")}
Doctor: Dr. {appointment.doctor.get_full_name()}
Description: {appointment.description}

Please be on time for your appointment. Please contact our clinic for any changes.

Sincerely,
Laso Healthcare Health System
"""
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.patient.email],
        fail_silently=False,
    )
    
    return True


def get_upcoming_appointments(days=1):
    """
    Returns upcoming appointments within the specified number of days
    """
    from appointments.models import Appointment
    
    tomorrow = timezone.now().date() + timedelta(days=days)
    
    return Appointment.objects.filter(
        date=tomorrow,
        status='planned'
    )
