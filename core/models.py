from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone


class Speciality(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="specialities/", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Speciality"
        verbose_name_plural = "Specialities"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("doctors:list") + f"?speciality={self.slug}"

    @property
    def doctor_count(self):
        return self.doctor_set.filter(is_active=True).count()

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return "/static/assets/img/specialities/default.png"


class Review(models.Model):
    RATING_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    patient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="reviews_given"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )
    booking = models.OneToOneField(
        "bookings.Booking", on_delete=models.CASCADE
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["patient", "booking"]

    def __str__(self):
        return f"Review by {self.patient} for Dr. {self.doctor}"

    @property
    def rating_percent(self):
        return (self.rating / 5) * 100


class SoapNote(models.Model):
    """
    SOAP Notes for patient appointments
    S - Subjective: Patient-reported symptoms, history, and concerns
    O - Objective: Observations, test results, vital signs
    A - Assessment: Doctor's diagnosis, impressions
    P - Plan: Treatment plan, follow-up instructions
    """
    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="soap_notes",
        limit_choices_to={"role": "patient"}
    )
    appointment = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="soap_notes"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="soap_notes_created",
        limit_choices_to={"role": "doctor"}
    )
    
    # SOAP Components
    subjective = models.TextField(
        help_text="Patient-reported symptoms, history, and concerns"
    )
    objective = models.TextField(
        help_text="Observations, test results, vital signs"
    )
    assessment = models.TextField(
        help_text="Doctor's diagnosis, impressions"
    )
    plan = models.TextField(
        help_text="Treatment plan, follow-up instructions"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_draft = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-created_at"]
        unique_together = ["appointment", "created_by"]
        verbose_name = "SOAP Note"
        verbose_name_plural = "SOAP Notes"

    def __str__(self):
        return f"SOAP Note for {self.patient.get_full_name()} - {self.appointment.appointment_date}"

    def clean(self):
        """Validate that the appointment belongs to the patient and doctor"""
        if self.appointment and self.patient:
            if self.appointment.patient != self.patient:
                raise ValidationError("Appointment must belong to the specified patient")
        
        if self.appointment and self.created_by:
            if self.appointment.doctor != self.created_by:
                raise ValidationError("Only the assigned doctor can create SOAP notes for this appointment")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class EHRRecord(models.Model):
    """
    Electronic Health Record for patients
    """
    patient = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="ehr_record",
        limit_choices_to={"role": "patient"}
    )
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="Known allergies and reactions")
    medications = models.TextField(blank=True, help_text="Current medications and dosages")
    medical_history = models.TextField(blank=True, help_text="Past medical conditions and surgeries")
    immunizations = models.TextField(blank=True, help_text="Immunization history")
    
    # Lab and Imaging Results (using JSONField for flexibility)
    lab_results = models.JSONField(default=dict, blank=True, help_text="Laboratory test results")
    imaging_results = models.JSONField(default=dict, blank=True, help_text="Imaging study results")
    
    # Vital Signs History
    vital_signs_history = models.JSONField(default=list, blank=True, help_text="Historical vital signs")
    
    # Emergency Contacts
    emergency_contacts = models.JSONField(default=list, blank=True, help_text="Emergency contact information")
    
    # Insurance Information
    insurance_info = models.JSONField(default=dict, blank=True, help_text="Insurance details")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ehr_records_updated"
    )

    class Meta:
        verbose_name = "EHR Record"
        verbose_name_plural = "EHR Records"

    def __str__(self):
        return f"EHR Record for {self.patient.get_full_name()}"

    def get_soap_notes(self):
        """Get all SOAP notes for this patient"""
        return self.patient.soap_notes.all()

    def get_recent_soap_notes(self, limit=10):
        """Get recent SOAP notes for this patient"""
        return self.patient.soap_notes.all()[:limit]

    def add_vital_signs(self, vital_signs_data):
        """Add new vital signs to history"""
        if not isinstance(self.vital_signs_history, list):
            self.vital_signs_history = []
        
        vital_signs_data['timestamp'] = timezone.now().isoformat()
        self.vital_signs_history.append(vital_signs_data)
        self.save()

    def add_lab_result(self, test_name, result_data):
        """Add new lab result"""
        if not isinstance(self.lab_results, dict):
            self.lab_results = {}
        
        if test_name not in self.lab_results:
            self.lab_results[test_name] = []
        
        result_data['timestamp'] = timezone.now().isoformat()
        self.lab_results[test_name].append(result_data)
        self.save()

    def add_imaging_result(self, study_type, result_data):
        """Add new imaging result"""
        if not isinstance(self.imaging_results, dict):
            self.imaging_results = {}
        
        if study_type not in self.imaging_results:
            self.imaging_results[study_type] = []
        
        result_data['timestamp'] = timezone.now().isoformat()
        self.imaging_results[study_type].append(result_data)
        self.save()


class AuditLog(models.Model):
    """
    Audit log for tracking changes to sensitive medical data
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.action} {self.model_name} by {self.user} at {self.timestamp}"


class HospitalSettings(models.Model):
    """
    Hospital configuration and settings
    """
    # Hospital Information
    hospital_name = models.CharField(max_length=200, default="Laso Digital Health")
    hospital_logo = models.ImageField(upload_to="hospital/", null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Bangladesh")
    
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # License and Certification
    license_number = models.CharField(max_length=100, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    accreditation = models.CharField(max_length=200, blank=True)
    
    # System Preferences
    timezone = models.CharField(max_length=50, default="Asia/Dhaka")
    date_format = models.CharField(
        max_length=20,
        choices=[
            ("%d/%m/%Y", "DD/MM/YYYY"),
            ("%m/%d/%Y", "MM/DD/YYYY"),
            ("%Y-%m-%d", "YYYY-MM-DD"),
        ],
        default="%d/%m/%Y"
    )
    time_format = models.CharField(
        max_length=10,
        choices=[
            ("12", "12 Hour"),
            ("24", "24 Hour"),
        ],
        default="12"
    )
    currency = models.CharField(max_length=10, default="BDT")
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    appointment_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.IntegerField(default=24)
    
    # Business Hours
    monday_open = models.TimeField(default="09:00")
    monday_close = models.TimeField(default="17:00")
    tuesday_open = models.TimeField(default="09:00")
    tuesday_close = models.TimeField(default="17:00")
    wednesday_open = models.TimeField(default="09:00")
    wednesday_close = models.TimeField(default="17:00")
    thursday_open = models.TimeField(default="09:00")
    thursday_close = models.TimeField(default="17:00")
    friday_open = models.TimeField(default="09:00")
    friday_close = models.TimeField(default="17:00")
    saturday_open = models.TimeField(default="09:00")
    saturday_close = models.TimeField(default="13:00")
    sunday_closed = models.BooleanField(default=True)
    sunday_open = models.TimeField(default="09:00", null=True, blank=True)
    sunday_close = models.TimeField(default="17:00", null=True, blank=True)
    
    # System Settings
    max_appointments_per_day = models.IntegerField(default=50)
    appointment_duration = models.IntegerField(default=30, help_text="Duration in minutes")
    allow_online_booking = models.BooleanField(default=True)
    require_payment_confirmation = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "accounts.User", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="hospital_settings_updates"
    )

    class Meta:
        verbose_name = "Hospital Settings"
        verbose_name_plural = "Hospital Settings"

    def __str__(self):
        return f"{self.hospital_name} Settings"

    @classmethod
    def get_settings(cls):
        """Get or create hospital settings"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'hospital_name': 'Laso Digital Health',
                'address': 'House 1, Road 1, Block A, Banani',
                'city': 'Dhaka',
                'state': 'Dhaka',
                'postal_code': '1213',
                'phone': '+880 1700-000000',
                'email': 'info@lasodigitalhealth.com',
            }
        )
        return settings
