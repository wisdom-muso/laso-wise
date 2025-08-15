from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Consultation, ConsultationMessage, ConsultationParticipant,
    ConsultationRecording, WaitingRoom, TechnicalIssue, VideoProviderConfig
)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'doctor_name', 'patient_name', 'appointment_date', 
        'appointment_time', 'status', 'video_provider', 'duration_display',
        'created_at'
    ]
    list_filter = [
        'status', 'video_provider', 'recording_enabled', 
        'created_at', 'scheduled_start'
    ]
    search_fields = [
        'doctor__first_name', 'doctor__last_name', 'doctor__email',
        'patient__first_name', 'patient__last_name', 'patient__email',
        'meeting_id', 'notes'
    ]
    readonly_fields = [
        'id', 'booking', 'doctor', 'patient', 'created_at', 'updated_at',
        'actual_start', 'actual_end', 'duration_minutes'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'booking', 'doctor', 'patient', 'status')
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'actual_start', 'actual_end', 'duration_minutes')
        }),
        ('Video Configuration', {
            'fields': ('video_provider', 'meeting_id', 'meeting_url', 'meeting_password')
        }),
        ('Settings', {
            'fields': ('recording_enabled', 'recording_url', 'connection_quality')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def doctor_name(self, obj):
        return obj.doctor.get_full_name()
    doctor_name.short_description = 'Doctor'
    doctor_name.admin_order_field = 'doctor__first_name'
    
    def patient_name(self, obj):
        return obj.patient.get_full_name()
    patient_name.short_description = 'Patient'
    patient_name.admin_order_field = 'patient__first_name'
    
    def appointment_date(self, obj):
        return obj.booking.appointment_date
    appointment_date.short_description = 'Date'
    appointment_date.admin_order_field = 'booking__appointment_date'
    
    def appointment_time(self, obj):
        return obj.booking.appointment_time
    appointment_time.short_description = 'Time'
    appointment_time.admin_order_field = 'booking__appointment_time'
    
    def duration_display(self, obj):
        if obj.duration_minutes:
            return f"{obj.duration_minutes} min"
        return "-"
    duration_display.short_description = 'Duration'


class ConsultationMessageInline(admin.TabularInline):
    model = ConsultationMessage
    extra = 0
    readonly_fields = ['sender', 'timestamp']
    fields = ['sender', 'message', 'message_type', 'is_private', 'timestamp']


class ConsultationParticipantInline(admin.TabularInline):
    model = ConsultationParticipant
    extra = 0
    readonly_fields = ['joined_at', 'left_at']


@admin.register(ConsultationMessage)
class ConsultationMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'consultation_link', 'sender_name', 'message_preview', 
        'message_type', 'is_private', 'timestamp'
    ]
    list_filter = ['message_type', 'is_private', 'timestamp']
    search_fields = [
        'message', 'sender__first_name', 'sender__last_name',
        'consultation__id'
    ]
    readonly_fields = ['consultation', 'sender', 'timestamp']
    
    def consultation_link(self, obj):
        url = reverse('admin:telemedicine_consultation_change', args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation.id)
    consultation_link.short_description = 'Consultation'
    
    def sender_name(self, obj):
        return obj.sender.get_full_name()
    sender_name.short_description = 'Sender'
    sender_name.admin_order_field = 'sender__first_name'
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


@admin.register(ConsultationParticipant)
class ConsultationParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'consultation_link', 'user_name', 'role', 
        'joined_at', 'left_at', 'connection_issues'
    ]
    list_filter = ['role', 'joined_at', 'left_at']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'consultation__id'
    ]
    
    def consultation_link(self, obj):
        url = reverse('admin:telemedicine_consultation_change', args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation.id)
    consultation_link.short_description = 'Consultation'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__first_name'


@admin.register(ConsultationRecording)
class ConsultationRecordingAdmin(admin.ModelAdmin):
    list_display = [
        'consultation_link', 'recording_id', 'file_size_mb', 
        'duration_seconds', 'is_processed', 'is_available', 'created_at'
    ]
    list_filter = ['is_processed', 'is_available', 'created_at']
    search_fields = ['recording_id', 'consultation__id']
    readonly_fields = ['consultation', 'created_at', 'updated_at']
    
    def consultation_link(self, obj):
        url = reverse('admin:telemedicine_consultation_change', args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation.id)
    consultation_link.short_description = 'Consultation'


@admin.register(WaitingRoom)
class WaitingRoomAdmin(admin.ModelAdmin):
    list_display = [
        'consultation_link', 'patient_name', 'patient_joined_at', 
        'doctor_notified_at', 'estimated_wait_minutes', 'queue_position'
    ]
    list_filter = ['patient_joined_at', 'doctor_notified_at']
    search_fields = ['consultation__id', 'consultation__patient__first_name']
    readonly_fields = ['consultation']
    
    def consultation_link(self, obj):
        url = reverse('admin:telemedicine_consultation_change', args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation.id)
    consultation_link.short_description = 'Consultation'
    
    def patient_name(self, obj):
        return obj.consultation.patient.get_full_name()
    patient_name.short_description = 'Patient'


@admin.register(TechnicalIssue)
class TechnicalIssueAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'consultation_link', 'reporter_name', 'issue_type', 
        'severity', 'resolved', 'created_at'
    ]
    list_filter = ['issue_type', 'severity', 'resolved', 'created_at']
    search_fields = [
        'description', 'reporter__first_name', 'reporter__last_name',
        'consultation__id'
    ]
    readonly_fields = ['consultation', 'reporter', 'created_at']
    fieldsets = (
        ('Issue Information', {
            'fields': ('consultation', 'reporter', 'issue_type', 'severity', 'description')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolution_notes')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def consultation_link(self, obj):
        url = reverse('admin:telemedicine_consultation_change', args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation.id)
    consultation_link.short_description = 'Consultation'
    
    def reporter_name(self, obj):
        return obj.reporter.get_full_name()
    reporter_name.short_description = 'Reporter'
    reporter_name.admin_order_field = 'reporter__first_name'
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} issues marked as resolved.')
    mark_resolved.short_description = 'Mark selected issues as resolved'


@admin.register(VideoProviderConfig)
class VideoProviderConfigAdmin(admin.ModelAdmin):
    list_display = [
        'provider', 'is_active', 'max_participants', 
        'recording_enabled', 'created_at'
    ]
    list_filter = ['provider', 'is_active', 'recording_enabled']
    search_fields = ['provider']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Provider Information', {
            'fields': ('provider', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'webhook_url')
        }),
        ('Settings', {
            'fields': ('max_participants', 'recording_enabled', 'settings_json')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )