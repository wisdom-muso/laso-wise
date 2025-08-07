from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import logging

from bookings.models import Booking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send appointment reminders to patients and doctors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Send reminders for appointments in X hours (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails'
        )

    def handle(self, *args, **options):
        hours_ahead = options['hours']
        dry_run = options['dry_run']
        
        # Calculate the target date/time
        now = timezone.now()
        target_time = now + timedelta(hours=hours_ahead)
        
        # Find appointments that need reminders
        appointments = Booking.objects.filter(
            appointment_date=target_time.date(),
            appointment_time__hour=target_time.hour,
            status__in=['pending', 'confirmed']
        ).select_related('patient', 'doctor', 'patient__profile', 'doctor__profile')
        
        reminder_count = 0
        
        for appointment in appointments:
            try:
                # Send reminder to patient
                self.send_patient_reminder(appointment, dry_run)
                
                # Send reminder to doctor
                self.send_doctor_reminder(appointment, dry_run)
                
                reminder_count += 1
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Sent reminders for appointment {appointment.id}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Would send reminders for appointment {appointment.id}'
                        )
                    )
                    
            except Exception as e:
                logger.error(f'Failed to send reminder for appointment {appointment.id}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder for appointment {appointment.id}: {str(e)}'
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] Would send {reminder_count * 2} reminder emails for {reminder_count} appointments'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent {reminder_count * 2} reminder emails for {reminder_count} appointments'
                )
            )

    def send_patient_reminder(self, appointment, dry_run=False):
        """Send appointment reminder to patient"""
        subject = f'Appointment Reminder - Dr. {appointment.doctor.get_full_name()}'
        
        context = {
            'appointment': appointment,
            'patient': appointment.patient,
            'doctor': appointment.doctor,
        }
        
        # Render email templates
        html_message = render_to_string('emails/patient_appointment_reminder.html', context)
        plain_message = render_to_string('emails/patient_appointment_reminder.txt', context)
        
        if not dry_run and appointment.patient.email:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient.email],
                html_message=html_message,
                fail_silently=False,
            )

    def send_doctor_reminder(self, appointment, dry_run=False):
        """Send appointment reminder to doctor"""
        subject = f'Appointment Reminder - {appointment.patient.get_full_name()}'
        
        context = {
            'appointment': appointment,
            'patient': appointment.patient,
            'doctor': appointment.doctor,
        }
        
        # Render email templates
        html_message = render_to_string('emails/doctor_appointment_reminder.html', context)
        plain_message = render_to_string('emails/doctor_appointment_reminder.txt', context)
        
        if not dry_run and appointment.doctor.email:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.doctor.email],
                html_message=html_message,
                fail_silently=False,
            )