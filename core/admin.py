from django.contrib import admin
from .models import Review, HospitalSettings


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'rating', 'created_at', 'rating_percent']
    list_filter = ['rating', 'created_at']
    search_fields = ['patient__username', 'patient__first_name', 'patient__last_name',
                    'doctor__username', 'doctor__first_name', 'doctor__last_name',
                    'review']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'rating_percent']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('patient', 'doctor', 'booking', 'rating', 'review')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'rating_percent'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_percent(self, obj):
        return f"{obj.rating_percent}%"
    rating_percent.short_description = "Rating Percentage"


@admin.register(HospitalSettings)
class HospitalSettingsAdmin(admin.ModelAdmin):
    list_display = ['hospital_name', 'city', 'phone', 'email', 'updated_at', 'updated_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Hospital Information', {
            'fields': ('hospital_name', 'hospital_logo', 'address', 'city', 'state', 
                      'postal_code', 'country')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website')
        }),
        ('License & Certification', {
            'fields': ('license_number', 'license_expiry', 'accreditation'),
            'classes': ('collapse',)
        }),
        ('System Preferences', {
            'fields': ('timezone', 'date_format', 'time_format', 'currency'),
            'classes': ('collapse',)
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications', 'appointment_reminders', 
                      'reminder_hours_before'),
            'classes': ('collapse',)
        }),
        ('Business Hours', {
            'fields': (
                ('monday_open', 'monday_close'),
                ('tuesday_open', 'tuesday_close'),
                ('wednesday_open', 'wednesday_close'),
                ('thursday_open', 'thursday_close'),
                ('friday_open', 'friday_close'),
                ('saturday_open', 'saturday_close'),
                ('sunday_closed', 'sunday_open', 'sunday_close'),
            ),
            'classes': ('collapse',)
        }),
        ('System Settings', {
            'fields': ('max_appointments_per_day', 'appointment_duration', 
                      'allow_online_booking', 'require_payment_confirmation'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        # Only allow one hospital settings instance
        return not HospitalSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of hospital settings
        return False
