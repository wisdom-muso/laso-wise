from django.contrib import admin
from .models import VitalCategory, VitalRecord, VitalGoal, VitalNotification


@admin.register(VitalCategory)
class VitalCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'min_normal', 'max_normal', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')


@admin.register(VitalRecord)
class VitalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'category', 'value', 'secondary_value', 'status_display', 'is_professional_reading', 'recorded_at')
    list_filter = ('category', 'is_professional_reading', 'recorded_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'notes')
    date_hierarchy = 'recorded_at'
    raw_id_fields = ('patient', 'recorded_by')


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