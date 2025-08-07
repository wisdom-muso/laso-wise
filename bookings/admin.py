from django.contrib import admin
from .models import Booking, Prescription, ProgressNote


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'booking_date']
    list_filter = ['status', 'appointment_date', 'booking_date']
    search_fields = ['patient__username', 'patient__first_name', 'patient__last_name', 
                    'doctor__username', 'doctor__first_name', 'doctor__last_name']
    date_hierarchy = 'appointment_date'
    ordering = ['-appointment_date', '-appointment_time']
    readonly_fields = ['booking_date']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status')
        }),
        ('Metadata', {
            'fields': ('booking_date',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'booking', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['patient__username', 'patient__first_name', 'patient__last_name',
                    'doctor__username', 'doctor__first_name', 'doctor__last_name',
                    'symptoms', 'diagnosis']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Patient & Doctor', {
            'fields': ('booking', 'patient', 'doctor')
        }),
        ('Medical Information', {
            'fields': ('symptoms', 'diagnosis', 'medications', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'doctor', 'note_type', 'is_private', 'created_at']
    list_filter = ['note_type', 'is_private', 'created_at', 'updated_at']
    search_fields = ['title', 'content', 'patient__username', 'patient__first_name', 
                    'patient__last_name', 'doctor__username', 'doctor__first_name', 
                    'doctor__last_name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Note Information', {
            'fields': ('title', 'note_type', 'is_private')
        }),
        ('Patient & Doctor', {
            'fields': ('booking', 'patient', 'doctor')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If user is not superuser, only show their own notes or public notes
        if not request.user.is_superuser:
            if hasattr(request.user, 'role') and request.user.role == 'doctor':
                qs = qs.filter(doctor=request.user)
            elif hasattr(request.user, 'role') and request.user.role == 'patient':
                qs = qs.filter(patient=request.user, is_private=False)
        return qs
