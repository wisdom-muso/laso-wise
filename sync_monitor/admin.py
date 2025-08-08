from django.contrib import admin
from .models import SyncStatus, SystemHealthCheck, DataSyncLog


@admin.register(SyncStatus)
class SyncStatusAdmin(admin.ModelAdmin):
    list_display = ('sync_type', 'status', 'started_at', 'completed_at', 'records_processed', 'records_failed', 'success_rate')
    list_filter = ('sync_type', 'status', 'started_at')
    search_fields = ('sync_type', 'error_message')
    readonly_fields = ('started_at', 'success_rate')
    
    fieldsets = (
        (None, {
            'fields': ('sync_type', 'status', 'initiated_by')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Results', {
            'fields': ('records_processed', 'records_failed', 'success_rate')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemHealthCheck)
class SystemHealthCheckAdmin(admin.ModelAdmin):
    list_display = ('check_type', 'status', 'response_time', 'checked_at')
    list_filter = ('check_type', 'status', 'checked_at')
    search_fields = ('check_type', 'details')
    readonly_fields = ('checked_at',)


@admin.register(DataSyncLog)
class DataSyncLogAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'action', 'success', 'timestamp')
    list_filter = ('entity_type', 'action', 'success', 'timestamp')
    search_fields = ('entity_type', 'entity_id', 'error_message')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        (None, {
            'fields': ('sync_status', 'entity_type', 'entity_id', 'action', 'success')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('timestamp',)
        }),
    )