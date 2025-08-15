from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class AppointmentType(models.TextChoices):
    IN_PERSON = 'in_person', 'In-Person'
    VIRTUAL = 'virtual', 'Virtual Consultation'


class Booking(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        limit_choices_to={"role": "doctor"},
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_appointments",
        limit_choices_to={"role": "patient"},
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    booking_date = models.DateTimeField(auto_now_add=True)
    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.IN_PERSON,
        help_text="Type of appointment (in-person or virtual consultation)"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No Show"),
        ],
        default="pending",
    )
    
    # Additional fields for virtual consultations
    consultation_notes = models.TextField(
        blank=True,
        help_text="Notes or special instructions for the consultation"
    )
    preferred_video_provider = models.CharField(
        max_length=20,
        choices=[
            ('jitsi', 'Jitsi Meet'),
            ('zoom', 'Zoom'),
            ('google_meet', 'Google Meet'),
        ],
        blank=True,
        help_text="Preferred video platform for virtual consultations"
    )

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]
        # Ensure no double bookings for same doctor at same time
        unique_together = ["doctor", "appointment_date", "appointment_time"]

    def __str__(self):
        appointment_type_str = " (Virtual)" if self.appointment_type == AppointmentType.VIRTUAL else ""
        return f"Appointment with Dr. {self.doctor.get_full_name()} on {self.appointment_date} at {self.appointment_time}{appointment_type_str}"
    
    @property
    def is_virtual(self):
        """Check if this is a virtual consultation"""
        return self.appointment_type == AppointmentType.VIRTUAL
    
    @property
    def has_consultation(self):
        """Check if this booking has an associated telemedicine consultation"""
        return hasattr(self, 'consultation')


class Prescription(models.Model):
    booking = models.OneToOneField(
        "Booking", on_delete=models.CASCADE, related_name="prescription"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_given",
    )
    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_received",
    )
    symptoms = models.TextField()
    diagnosis = models.TextField()
    medications = RichTextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prescription for {self.patient} by Dr. {self.doctor}"

    class Meta:
        ordering = ["-created_at"]


class ProgressNote(models.Model):
    """
    Progress notes for patient appointments
    """
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name="progress_notes"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="progress_notes_written",
        limit_choices_to={"role": "doctor"}
    )
    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="progress_notes_received",
        limit_choices_to={"role": "patient"}
    )
    note_type = models.CharField(
        max_length=20,
        choices=[
            ("consultation", "Consultation Note"),
            ("follow_up", "Follow-up Note"),
            ("treatment", "Treatment Note"),
            ("observation", "Observation"),
            ("discharge", "Discharge Note"),
        ],
        default="consultation"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_private = models.BooleanField(
        default=False, 
        help_text="Private notes are only visible to healthcare providers"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.patient.get_full_name()}"
