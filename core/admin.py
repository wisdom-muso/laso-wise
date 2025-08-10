from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Speciality, Review, HospitalSettings, 
    SoapNote, EHRRecord, AuditLog
)


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "doctor_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]

    def doctor_count(self, obj):
        return obj.doctor_count

    doctor_count.short_description = "Number of Doctors"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "patient", "doctor", "rating", "booking", "created_at"
    ]
    list_filter = ["rating", "created_at"]
    search_fields = [
        "patient__first_name", "patient__last_name", 
        "doctor__first_name", "doctor__last_name"
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "patient", "doctor", "booking"
        )


@admin.register(SoapNote)
class SoapNoteAdmin(admin.ModelAdmin):
    list_display = [
        "patient", "doctor", "appointment_date", "is_draft", "created_at"
    ]
    list_filter = ["is_draft", "created_at", "created_by__profile__specialization"]
    search_fields = [
        "patient__first_name", "patient__last_name",
        "created_by__first_name", "created_by__last_name",
        "subjective", "objective", "assessment", "plan"
    ]
    readonly_fields = ["created_at", "updated_at", "patient_link", "doctor_link", "appointment_link"]
    fieldsets = (
        ("Patient Information", {
            "fields": ("patient_link", "doctor_link", "appointment_link")
        }),
        ("SOAP Components", {
            "fields": ("subjective", "objective", "assessment", "plan")
        }),
        ("Metadata", {
            "fields": ("is_draft", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    ordering = ["-created_at"]

    def patient_link(self, obj):
        if obj.patient:
            url = reverse("admin:accounts_user_change", args=[obj.patient.id])
            return format_html('<a href="{}">{}</a>', url, obj.patient.get_full_name())
        return "-"
    patient_link.short_description = "Patient"

    def doctor_link(self, obj):
        if obj.created_by:
            url = reverse("admin:accounts_user_change", args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.get_full_name())
        return "-"
    doctor_link.short_description = "Doctor"

    def appointment_link(self, obj):
        if obj.appointment:
            url = reverse("admin:bookings_booking_change", args=[obj.appointment.id])
            return format_html('<a href="{}">{}</a>', url, f"{obj.appointment.appointment_date} at {obj.appointment.appointment_time}")
        return "-"
    appointment_link.short_description = "Appointment"

    def appointment_date(self, obj):
        return obj.appointment.appointment_date if obj.appointment else "-"
    appointment_date.short_description = "Appointment Date"

    def doctor(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else "-"
    doctor.short_description = "Doctor"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "patient", "patient__profile", "created_by", "created_by__profile", "appointment"
        )


@admin.register(EHRRecord)
class EHRRecordAdmin(admin.ModelAdmin):
    list_display = [
        "patient", "has_allergies", "has_medications", "soap_notes_count", "updated_at"
    ]
    list_filter = ["created_at", "updated_at", "last_updated_by"]
    search_fields = [
        "patient__first_name", "patient__last_name", "patient__username",
        "allergies", "medications", "medical_history"
    ]
    readonly_fields = [
        "created_at", "updated_at", "patient_link", "last_updated_by_link",
        "soap_notes_count", "vital_signs_count", "lab_results_count", "imaging_results_count"
    ]
    fieldsets = (
        ("Patient Information", {
            "fields": ("patient_link", "last_updated_by_link")
        }),
        ("Medical Information", {
            "fields": ("allergies", "medications", "medical_history", "immunizations")
        }),
        ("Lab & Imaging Results", {
            "fields": ("lab_results", "imaging_results"),
            "classes": ("collapse",)
        }),
        ("Vital Signs & Contacts", {
            "fields": ("vital_signs_history", "emergency_contacts", "insurance_info"),
            "classes": ("collapse",)
        }),
        ("Statistics", {
            "fields": ("soap_notes_count", "vital_signs_count", "lab_results_count", "imaging_results_count"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    ordering = ["-updated_at"]

    def patient_link(self, obj):
        if obj.patient:
            url = reverse("admin:accounts_user_change", args=[obj.patient.id])
            return format_html('<a href="{}">{}</a>', url, obj.patient.get_full_name())
        return "-"
    patient_link.short_description = "Patient"

    def last_updated_by_link(self, obj):
        if obj.last_updated_by:
            url = reverse("admin:accounts_user_change", args=[obj.last_updated_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.last_updated_by.get_full_name())
        return "-"
    last_updated_by_link.short_description = "Last Updated By"

    def has_allergies(self, obj):
        return bool(obj.allergies and obj.allergies.strip())
    has_allergies.boolean = True
    has_allergies.short_description = "Has Allergies"

    def has_medications(self, obj):
        return bool(obj.medications and obj.medications.strip())
    has_medications.boolean = True
    has_medications.short_description = "Has Medications"

    def soap_notes_count(self, obj):
        return obj.patient.soap_notes.count()
    soap_notes_count.short_description = "SOAP Notes"

    def vital_signs_count(self, obj):
        if isinstance(obj.vital_signs_history, list):
            return len(obj.vital_signs_history)
        return 0
    vital_signs_count.short_description = "Vital Signs Records"

    def lab_results_count(self, obj):
        if isinstance(obj.lab_results, dict):
            return sum(len(results) for results in obj.lab_results.values())
        return 0
    lab_results_count.short_description = "Lab Results"

    def imaging_results_count(self, obj):
        if isinstance(obj.imaging_results, dict):
            return sum(len(results) for results in obj.imaging_results.values())
        return 0
    imaging_results_count.short_description = "Imaging Results"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "patient", "patient__profile", "last_updated_by"
        )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "user", "action", "model_name", "object_repr", "timestamp"
    ]
    list_filter = ["action", "model_name", "timestamp", "user__role"]
    search_fields = [
        "user__first_name", "user__last_name", "user__username",
        "model_name", "object_repr", "ip_address"
    ]
    readonly_fields = "__all__"
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(HospitalSettings)
class HospitalSettingsAdmin(admin.ModelAdmin):
    list_display = ["hospital_name", "city", "phone", "email"]
    fieldsets = (
        ("Hospital Information", {
            "fields": ("hospital_name", "hospital_logo", "address", "city", "state", "postal_code", "country")
        }),
        ("Contact Information", {
            "fields": ("phone", "email", "website")
        }),
        ("License and Certification", {
            "fields": ("license_number", "license_expiry", "accreditation"),
            "classes": ("collapse",)
        }),
        ("System Preferences", {
            "fields": ("timezone", "date_format", "time_format", "currency")
        }),
        ("Notification Settings", {
            "fields": ("email_notifications", "sms_notifications", "appointment_reminders", "reminder_hours_before")
        }),
        ("Business Hours", {
            "fields": (
                "monday_open", "monday_close", "tuesday_open", "tuesday_close",
                "wednesday_open", "wednesday_close", "thursday_open", "thursday_close",
                "friday_open", "friday_close", "saturday_open", "saturday_close",
                "sunday_closed", "sunday_open", "sunday_close"
            ),
            "classes": ("collapse",)
        }),
        ("System Settings", {
            "fields": ("max_appointments_per_day", "appointment_duration", "allow_online_booking", "require_payment_confirmation")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        # Only allow one hospital settings instance
        return not HospitalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
