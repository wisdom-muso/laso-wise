from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status')
    list_filter = ('status', 'date', 'doctor')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 
                    'doctor__username', 'doctor__first_name', 'doctor__last_name')
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor')
        }),
        (_('Randevu Bilgileri'), {
            'fields': ('date', 'time', 'description', 'status')
        }),
    )

# Doktor uygunluk sistemleri için admin kayıtları
try:
    from .models_availability import DoctorAvailability, DoctorTimeOff
    
    @admin.register(DoctorAvailability)
    class DoctorAvailabilityAdmin(admin.ModelAdmin):
        list_display = ('doctor', 'get_weekday_name', 'start_time', 'end_time', 'is_active')
        list_filter = ('weekday', 'is_active', 'doctor')
        search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name')
    
    @admin.register(DoctorTimeOff)
    class DoctorTimeOffAdmin(admin.ModelAdmin):
        list_display = ('doctor', 'start_date', 'end_date', 'is_full_day', 'reason')
        list_filter = ('is_full_day', 'start_date', 'doctor')
        search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name', 'reason')
        date_hierarchy = 'start_date'
except ImportError:
    pass
