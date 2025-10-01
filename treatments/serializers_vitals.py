"""
Serializers for Vital Signs REST API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models_vitals import VitalSign, VitalSignAlert

User = get_user_model()


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for patient information in vitals"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'full_name', 'email']


class RecordedBySerializer(serializers.ModelSerializer):
    """Serializer for the user who recorded the vitals"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'user_type']
        read_only_fields = ['id', 'username', 'full_name', 'user_type']


class VitalSignSerializer(serializers.ModelSerializer):
    """Serializer for VitalSign model"""
    patient_info = PatientSerializer(source='patient', read_only=True)
    recorded_by_info = RecordedBySerializer(source='recorded_by', read_only=True)
    blood_pressure_display = serializers.CharField(read_only=True)
    bp_category = serializers.CharField(read_only=True)
    bmi = serializers.DecimalField(max_digits=4, decimal_places=1, read_only=True)
    
    class Meta:
        model = VitalSign
        fields = [
            'id', 'patient', 'patient_info', 'recorded_by', 'recorded_by_info',
            'systolic_bp', 'diastolic_bp', 'blood_pressure_display', 'bp_category',
            'heart_rate', 'temperature', 'respiratory_rate', 'oxygen_saturation',
            'weight', 'height', 'bmi', 'cholesterol_total', 'cholesterol_ldl',
            'cholesterol_hdl', 'blood_glucose', 'cardiovascular_risk_score',
            'overall_risk_level', 'notes', 'measurement_context',
            'recorded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'patient_info', 'recorded_by_info', 'blood_pressure_display',
            'bp_category', 'bmi', 'overall_risk_level', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate vital sign data"""
        systolic = data.get('systolic_bp')
        diastolic = data.get('diastolic_bp')
        
        if systolic and diastolic and systolic <= diastolic:
            raise serializers.ValidationError(
                "Systolic blood pressure must be higher than diastolic blood pressure."
            )
        
        # Validate cholesterol values
        total_chol = data.get('cholesterol_total')
        ldl_chol = data.get('cholesterol_ldl')
        hdl_chol = data.get('cholesterol_hdl')
        
        if total_chol and ldl_chol and hdl_chol:
            if ldl_chol + hdl_chol > total_chol:
                raise serializers.ValidationError(
                    "LDL + HDL cholesterol cannot exceed total cholesterol."
                )
        
        return data


class VitalSignSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for vital sign summaries"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    blood_pressure_display = serializers.CharField(read_only=True)
    bp_category = serializers.CharField(read_only=True)
    
    class Meta:
        model = VitalSign
        fields = [
            'id', 'patient', 'patient_name', 'systolic_bp', 'diastolic_bp',
            'blood_pressure_display', 'bp_category', 'heart_rate',
            'overall_risk_level', 'recorded_at'
        ]


class VitalSignAlertSerializer(serializers.ModelSerializer):
    """Serializer for VitalSignAlert model"""
    vital_sign_info = VitalSignSummarySerializer(source='vital_sign', read_only=True)
    patient_name = serializers.CharField(source='vital_sign.patient.get_full_name', read_only=True)
    acknowledged_by_info = RecordedBySerializer(source='acknowledged_by', read_only=True)
    
    class Meta:
        model = VitalSignAlert
        fields = [
            'id', 'vital_sign', 'vital_sign_info', 'patient_name',
            'alert_type', 'severity', 'message', 'status',
            'acknowledged_by', 'acknowledged_by_info', 'acknowledged_at',
            'created_at'
        ]
        read_only_fields = [
            'id', 'vital_sign_info', 'patient_name', 'acknowledged_by_info',
            'created_at'
        ]


class VitalSignTrendSerializer(serializers.Serializer):
    """Serializer for vital sign trend data"""
    date = serializers.DateField()
    systolic_bp = serializers.IntegerField()
    diastolic_bp = serializers.IntegerField()
    heart_rate = serializers.IntegerField()
    overall_risk_level = serializers.CharField()


class VitalSignStatsSerializer(serializers.Serializer):
    """Serializer for vital sign statistics"""
    total_records = serializers.IntegerField()
    avg_systolic = serializers.DecimalField(max_digits=5, decimal_places=1)
    avg_diastolic = serializers.DecimalField(max_digits=5, decimal_places=1)
    avg_heart_rate = serializers.DecimalField(max_digits=5, decimal_places=1)
    max_systolic = serializers.IntegerField()
    min_systolic = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    normal_count = serializers.IntegerField()
    last_recorded = serializers.DateTimeField()


class PatientVitalsDashboardSerializer(serializers.Serializer):
    """Serializer for patient vitals dashboard data"""
    patient = PatientSerializer()
    latest_vital = VitalSignSerializer()
    recent_vitals = VitalSignSerializer(many=True)
    active_alerts = VitalSignAlertSerializer(many=True)
    stats = VitalSignStatsSerializer()
    trend_data = VitalSignTrendSerializer(many=True)


class QuickVitalSignSerializer(serializers.ModelSerializer):
    """Simplified serializer for quick vital sign entry"""
    
    class Meta:
        model = VitalSign
        fields = [
            'patient', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'notes'
        ]
    
    def validate(self, data):
        """Basic validation for quick entry"""
        systolic = data.get('systolic_bp')
        diastolic = data.get('diastolic_bp')
        
        if systolic and diastolic and systolic <= diastolic:
            raise serializers.ValidationError(
                "Systolic blood pressure must be higher than diastolic blood pressure."
            )
        
        return data


class VitalSignBulkSerializer(serializers.Serializer):
    """Serializer for bulk vital sign operations"""
    vital_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(
        choices=['delete', 'export', 'mark_reviewed']
    )
    
    def validate_vital_ids(self, value):
        """Validate that all vital IDs exist"""
        existing_ids = VitalSign.objects.filter(id__in=value).values_list('id', flat=True)
        missing_ids = set(value) - set(existing_ids)
        
        if missing_ids:
            raise serializers.ValidationError(
                f"Vital signs with IDs {list(missing_ids)} do not exist."
            )
        
        return value