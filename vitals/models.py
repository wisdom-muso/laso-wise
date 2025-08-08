from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class VitalCategory(models.Model):
    """
    Categories for vital signs (e.g., Blood Pressure, Heart Rate, etc.)
    """
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    unit = models.CharField(_("Unit of Measurement"), max_length=50)
    icon = models.CharField(_("Icon Class"), max_length=50, default="fas fa-heartbeat")
    color = models.CharField(_("Color Code"), max_length=20, default="#3498db")
    
    # Normal range values
    min_normal = models.FloatField(_("Minimum Normal Value"), null=True, blank=True)
    max_normal = models.FloatField(_("Maximum Normal Value"), null=True, blank=True)
    
    # Critical range values
    min_critical = models.FloatField(_("Minimum Critical Value"), null=True, blank=True)
    max_critical = models.FloatField(_("Maximum Critical Value"), null=True, blank=True)
    
    display_order = models.PositiveSmallIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Vital Category")
        verbose_name_plural = _("Vital Categories")
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name


class VitalRecord(models.Model):
    """
    Individual vital sign records for patients
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="vital_records",
        limit_choices_to={"role": "patient"}
    )
    category = models.ForeignKey(
        VitalCategory, 
        on_delete=models.CASCADE,
        related_name="records"
    )
    value = models.FloatField(_("Value"))
    
    # Optional secondary value (e.g., diastolic for blood pressure)
    secondary_value = models.FloatField(_("Secondary Value"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Who recorded this vital sign
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_vitals"
    )
    
    # Was this recorded by a healthcare professional
    is_professional_reading = models.BooleanField(_("Professional Reading"), default=False)
    
    # Timestamps
    recorded_at = models.DateTimeField(_("Recorded At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Vital Record")
        verbose_name_plural = _("Vital Records")
        ordering = ["-recorded_at"]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.category.name}: {self.value} {self.category.unit}"
    
    @property
    def status(self):
        """
        Returns the status of the vital sign based on normal and critical ranges
        """
        if self.category.min_critical is not None and self.value < self.category.min_critical:
            return "critical-low"
        if self.category.max_critical is not None and self.value > self.category.max_critical:
            return "critical-high"
        if self.category.min_normal is not None and self.value < self.category.min_normal:
            return "abnormal-low"
        if self.category.max_normal is not None and self.value > self.category.max_normal:
            return "abnormal-high"
        return "normal"
    
    @property
    def status_display(self):
        """
        Returns a human-readable status
        """
        status_map = {
            "critical-low": _("Critical Low"),
            "critical-high": _("Critical High"),
            "abnormal-low": _("Below Normal"),
            "abnormal-high": _("Above Normal"),
            "normal": _("Normal"),
        }
        return status_map.get(self.status, _("Unknown"))
    
    @property
    def status_color(self):
        """
        Returns a color code for the status
        """
        status_colors = {
            "critical-low": "#e74c3c",  # Red
            "critical-high": "#e74c3c",  # Red
            "abnormal-low": "#f39c12",  # Orange
            "abnormal-high": "#f39c12",  # Orange
            "normal": "#2ecc71",  # Green
        }
        return status_colors.get(self.status, "#95a5a6")  # Default gray


class VitalGoal(models.Model):
    """
    Goals for vital signs set by patients or doctors
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="vital_goals",
        limit_choices_to={"role": "patient"}
    )
    category = models.ForeignKey(
        VitalCategory, 
        on_delete=models.CASCADE,
        related_name="goals"
    )
    
    target_value = models.FloatField(_("Target Value"))
    target_date = models.DateField(_("Target Date"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Who set this goal
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="set_vital_goals"
    )
    
    is_achieved = models.BooleanField(_("Achieved"), default=False)
    achieved_date = models.DateField(_("Date Achieved"), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Vital Goal")
        verbose_name_plural = _("Vital Goals")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.category.name} Goal: {self.target_value} {self.category.unit}"


class VitalNotification(models.Model):
    """
    Notifications for abnormal vital signs
    """
    SEVERITY_CHOICES = (
        ('info', _('Information')),
        ('warning', _('Warning')),
        ('danger', _('Danger')),
    )
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="vital_notifications",
        limit_choices_to={"role": "patient"}
    )
    vital_record = models.ForeignKey(
        VitalRecord,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    
    message = models.TextField(_("Message"))
    severity = models.CharField(_("Severity"), max_length=20, choices=SEVERITY_CHOICES, default='info')
    
    is_read = models.BooleanField(_("Read"), default=False)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Vital Notification")
        verbose_name_plural = _("Vital Notifications")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Notification for {self.patient.get_full_name()} - {self.vital_record.category.name}"