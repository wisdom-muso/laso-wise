"""
Django management command to remove demo/sample data from the system
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from appointments.models import Appointment
from treatments.models import Treatment, Prescription, LabTest, MedicalImage, Report
from core.models_communication import CommunicationNotification, Message
from core.models_notifications import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Remove demo/sample data from the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of demo data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete all demo data including:\n'
                    '- Sample users (except admin)\n'
                    '- Sample appointments\n'
                    '- Sample treatments\n'
                    '- Sample notifications\n'
                    '- Sample messages\n\n'
                    'Run with --confirm to proceed'
                )
            )
            return

        self.stdout.write('🧹 Cleaning up demo data...')
        
        try:
            with transaction.atomic():
                # Delete sample notifications and messages
                deleted_notifications = CommunicationNotification.objects.all().delete()[0]
                deleted_messages = Message.objects.all().delete()[0]
                deleted_system_notifications = Notification.objects.all().delete()[0]
                
                self.stdout.write(f'  ❌ Deleted {deleted_notifications} communication notifications')
                self.stdout.write(f'  ❌ Deleted {deleted_messages} messages')
                self.stdout.write(f'  ❌ Deleted {deleted_system_notifications} system notifications')

                # Delete sample medical data
                deleted_prescriptions = Prescription.objects.all().delete()[0]
                deleted_lab_tests = LabTest.objects.all().delete()[0]
                deleted_medical_images = MedicalImage.objects.all().delete()[0]
                deleted_reports = Report.objects.all().delete()[0]
                
                self.stdout.write(f'  ❌ Deleted {deleted_prescriptions} prescriptions')
                self.stdout.write(f'  ❌ Deleted {deleted_lab_tests} lab tests')
                self.stdout.write(f'  ❌ Deleted {deleted_medical_images} medical images')
                self.stdout.write(f'  ❌ Deleted {deleted_reports} reports')

                # Delete sample treatments
                deleted_treatments = Treatment.objects.all().delete()[0]
                self.stdout.write(f'  ❌ Deleted {deleted_treatments} treatments')

                # Delete sample appointments
                deleted_appointments = Appointment.objects.all().delete()[0]
                self.stdout.write(f'  ❌ Deleted {deleted_appointments} appointments')

                # Delete sample users (keep admin users)
                sample_users = User.objects.exclude(
                    user_type='admin'
                ).exclude(
                    is_superuser=True
                ).exclude(
                    username__in=['admin', 'administrator']
                )
                
                deleted_users = sample_users.delete()[0]
                self.stdout.write(f'  ❌ Deleted {deleted_users} sample users')

                self.stdout.write(
                    self.style.SUCCESS('✅ Demo data cleanup completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
            )
            raise