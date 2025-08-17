from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import VitalCategory, VitalRecord, VitalGoal, VitalNotification


@admin.register(VitalCategory)
class VitalCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'min_normal', 'max_normal', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')


@admin.register(VitalRecord)
class VitalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'category', 'value', 'secondary_value', 'status_display', 'is_professional_reading', 'recorded_at', 'analytics_link')
    list_filter = ('category', 'is_professional_reading', 'recorded_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'notes')
    date_hierarchy = 'recorded_at'
    raw_id_fields = ('patient', 'recorded_by')
    actions = ['view_analytics_for_selected']
    
    def analytics_link(self, obj):
        """Link to enhanced dashboard analytics"""
        url = reverse('core:enhanced-admin-dashboard')
        return format_html('<a href="{}#vitals" class="button">📊 View Analytics</a>', url)
    analytics_link.short_description = 'Analytics'
    
    def view_analytics_for_selected(self, request, queryset):
        """Custom action to view analytics for selected records"""
        self.message_user(request, f'Analytics available in the Enhanced Dashboard for {queryset.count()} records.')
        return None
    view_analytics_for_selected.short_description = "View analytics for selected records"


@admin.register(VitalGoal)
class VitalGoalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'category', 'target_value', 'target_date', 'is_achieved', 'achieved_date')
    list_filter = ('category', 'is_achieved', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'notes')
    date_hierarchy = 'created_at'
    raw_id_fields = ('patient', 'set_by')


@admin.register(VitalNotification)
class VitalNotificationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'severity', 'is_read', 'created_at')
    list_filter = ('severity', 'is_read', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'message')
    date_hierarchy = 'created_at'
    raw_id_fields = ('patient', 'vital_record')