from django.contrib import admin
from .models import MobileClinicRequest, MobileClinicNotification

@admin.register(MobileClinicRequest)
class MobileClinicRequestAdmin(admin.ModelAdmin):
    list_display = ('patient', 'requested_date', 'requested_time', 'status', 'created_at')
    list_filter = ('status', 'requested_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'address', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),
        ('Request Details', {
            'fields': ('requested_date', 'requested_time', 'address', 'reason', 'notes')
        }),
        ('Status Information', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(MobileClinicNotification)
class MobileClinicNotificationAdmin(admin.ModelAdmin):
    list_display = ('request', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'request__patient__first_name', 'request__patient__last_name')
    readonly_fields = ('created_at',)