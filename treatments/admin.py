from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Treatment, Prescription
# Using default admin site

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1

class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'get_doctor', 'get_date', 'diagnosis')
    list_filter = ('appointment__doctor', 'appointment__date')
    search_fields = ('diagnosis', 'notes', 'appointment__patient__username', 
                    'appointment__patient__first_name', 'appointment__patient__last_name')
    inlines = [PrescriptionInline]
    
    def get_patient(self, obj):
        return obj.appointment.patient
    get_patient.short_description = _('Patient')
    get_patient.admin_order_field = 'appointment__patient__username'
    
    def get_doctor(self, obj):
        return obj.appointment.doctor
    get_doctor.short_description = _('Doctor')
    get_doctor.admin_order_field = 'appointment__doctor__username'
    
    def get_date(self, obj):
        return obj.appointment.date
    get_date.short_description = _('Date')
    get_date.admin_order_field = 'appointment__date'

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'dosage', 'get_patient', 'get_doctor')
    list_filter = ('treatment__appointment__doctor', 'treatment__appointment__date')
    search_fields = ('name', 'dosage', 'instructions')
    
    def get_patient(self, obj):
        return obj.treatment.appointment.patient
    get_patient.short_description = _('Patient')
    
    def get_doctor(self, obj):
        return obj.treatment.appointment.doctor
    get_doctor.short_description = _('Doctor')

# Admin registrations for new models
try:
    from .models_medical_history import MedicalHistory

    class MedicalHistoryAdmin(admin.ModelAdmin):
        list_display = ('patient', 'condition_type', 'condition_name', 'diagnosed_date', 'is_active')
        list_filter = ('condition_type', 'is_active', 'diagnosed_date')
        search_fields = ('condition_name', 'notes', 'patient__username', 'patient__first_name', 'patient__last_name')
        date_hierarchy = 'diagnosed_date'
    
    admin.site.register(MedicalHistory, MedicalHistoryAdmin)
except ImportError:
    pass

try:
    from .models_lab import LabTest, TestResult

    class TestResultInline(admin.StackedInline):
        model = TestResult
        can_delete = False
        
    @admin.register(LabTest)
    class LabTestAdmin(admin.ModelAdmin):
        list_display = ('test_name', 'patient', 'doctor', 'status', 'requested_date', 'completed_date')
        list_filter = ('status', 'requested_date', 'doctor')
        search_fields = ('test_name', 'test_details', 'patient__username', 'patient__first_name', 'patient__last_name')
        inlines = [TestResultInline]
        date_hierarchy = 'requested_date'
        
    @admin.register(TestResult)
    class TestResultAdmin(admin.ModelAdmin):
        list_display = ('get_test_name', 'get_patient', 'is_normal', 'created_at')
        list_filter = ('is_normal', 'created_at')
        search_fields = ('result_text', 'notes', 'lab_test__test_name', 'lab_test__patient__username')
        
        def get_test_name(self, obj):
            return obj.lab_test.test_name
        get_test_name.short_description = _('Test Name')
        
        def get_patient(self, obj):
            return obj.lab_test.patient
        get_patient.short_description = _('Patient')
except ImportError:
    pass

try:
    from .models_medications import Medication, MedicationInteraction
    
    @admin.register(Medication)
    class MedicationAdmin(admin.ModelAdmin):
        list_display = ('name', 'active_ingredient', 'is_prescription', 'drug_code')
        list_filter = ('is_prescription', 'created_at')
        search_fields = ('name', 'active_ingredient', 'description', 'drug_code')
        
    @admin.register(MedicationInteraction)
    class MedicationInteractionAdmin(admin.ModelAdmin):
        list_display = ('medication1', 'medication2', 'severity')
        list_filter = ('severity',)
        search_fields = ('medication1__name', 'medication2__name', 'description', 'recommendations')
except ImportError:
    pass

try:
    from .models_imaging import MedicalImage, Report
    
    @admin.register(MedicalImage)
    class MedicalImageAdmin(admin.ModelAdmin):
        list_display = ('patient', 'image_type', 'body_part', 'doctor', 'taken_date')
        list_filter = ('image_type', 'taken_date', 'doctor')
        search_fields = ('body_part', 'description', 'patient__username', 'patient__first_name', 'patient__last_name')
        date_hierarchy = 'taken_date'
        
    @admin.register(Report)
    class ReportAdmin(admin.ModelAdmin):
        list_display = ('patient', 'report_type', 'title', 'doctor', 'valid_from', 'valid_until')
        list_filter = ('report_type', 'valid_from', 'doctor')
        search_fields = ('title', 'content', 'patient__username', 'patient__first_name', 'patient__last_name')
        date_hierarchy = 'valid_from'
except ImportError:
    pass

try:
    from .models_vitals import VitalSign, VitalSignAlert
    
    class VitalSignAlertInline(admin.TabularInline):
        model = VitalSignAlert
        extra = 0
        readonly_fields = ('created_at', 'acknowledged_at')
        fields = ('alert_type', 'severity', 'message', 'status', 'acknowledged_by', 'acknowledged_at')
    
    @admin.register(VitalSign)
    class VitalSignAdmin(admin.ModelAdmin):
        list_display = (
            'patient', 'blood_pressure_display', 'heart_rate', 'overall_risk_level',
            'recorded_by', 'recorded_at'
        )
        list_filter = (
            'overall_risk_level', 'recorded_at', 'recorded_by',
            'patient__gender'
        )
        search_fields = (
            'patient__username', 'patient__first_name', 'patient__last_name',
            'notes', 'measurement_context'
        )
        date_hierarchy = 'recorded_at'
        readonly_fields = ('overall_risk_level', 'bp_category', 'bmi', 'created_at', 'updated_at')
        inlines = [VitalSignAlertInline]
        
        fieldsets = (
            (_('Patient Information'), {
                'fields': ('patient', 'recorded_by', 'recorded_at')
            }),
            (_('Vital Signs'), {
                'fields': (
                    ('systolic_bp', 'diastolic_bp'),
                    'heart_rate',
                    ('temperature', 'respiratory_rate', 'oxygen_saturation'),
                    ('weight', 'height')
                )
            }),
            (_('Lab Values'), {
                'fields': (
                    ('cholesterol_total', 'cholesterol_ldl', 'cholesterol_hdl'),
                    'blood_glucose'
                ),
                'classes': ('collapse',)
            }),
            (_('Risk Assessment'), {
                'fields': ('cardiovascular_risk_score', 'overall_risk_level', 'bp_category', 'bmi'),
                'classes': ('collapse',)
            }),
            (_('Additional Information'), {
                'fields': ('notes', 'measurement_context'),
                'classes': ('collapse',)
            }),
            (_('Timestamps'), {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            })
        )
        
        def get_queryset(self, request):
            return super().get_queryset(request).select_related('patient', 'recorded_by')
        
        def bp_category(self, obj):
            return obj.get_bp_category_display()
        bp_category.short_description = _('BP Category')
        
        def has_change_permission(self, request, obj=None):
            if obj and request.user.is_authenticated:
                # Only allow editing by the recorder or superuser
                return request.user.is_superuser or obj.recorded_by == request.user
            return super().has_change_permission(request, obj)
    
    @admin.register(VitalSignAlert)
    class VitalSignAlertAdmin(admin.ModelAdmin):
        list_display = (
            'get_patient', 'alert_type', 'severity', 'status',
            'acknowledged_by', 'created_at'
        )
        list_filter = (
            'alert_type', 'severity', 'status', 'created_at',
            'vital_sign__patient__gender'
        )
        search_fields = (
            'vital_sign__patient__username', 'vital_sign__patient__first_name',
            'vital_sign__patient__last_name', 'message'
        )
        date_hierarchy = 'created_at'
        readonly_fields = ('created_at', 'acknowledged_at')
        
        fieldsets = (
            (_('Alert Information'), {
                'fields': ('vital_sign', 'alert_type', 'severity', 'message')
            }),
            (_('Status'), {
                'fields': ('status', 'acknowledged_by', 'acknowledged_at')
            }),
            (_('Notifications'), {
                'fields': ('notified_users',),
                'classes': ('collapse',)
            }),
            (_('Timestamps'), {
                'fields': ('created_at',),
                'classes': ('collapse',)
            })
        )
        
        def get_patient(self, obj):
            return obj.vital_sign.patient
        get_patient.short_description = _('Patient')
        get_patient.admin_order_field = 'vital_sign__patient__username'
        
        def get_queryset(self, request):
            return super().get_queryset(request).select_related(
                'vital_sign__patient', 'acknowledged_by'
            ).prefetch_related('notified_users')
        
        actions = ['mark_acknowledged', 'mark_resolved']
        
        def mark_acknowledged(self, request, queryset):
            updated = queryset.filter(status='active').update(
                status='acknowledged',
                acknowledged_by=request.user,
                acknowledged_at=timezone.now()
            )
            self.message_user(
                request,
                f'{updated} alerts marked as acknowledged.'
            )
        mark_acknowledged.short_description = _('Mark selected alerts as acknowledged')
        
        def mark_resolved(self, request, queryset):
            updated = queryset.exclude(status='resolved').update(status='resolved')
            self.message_user(
                request,
                f'{updated} alerts marked as resolved.'
            )
        mark_resolved.short_description = _('Mark selected alerts as resolved')

except ImportError:
    pass

# Register all models with custom admin site
admin.site.register(Treatment, TreatmentAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
