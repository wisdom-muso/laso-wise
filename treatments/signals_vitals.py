"""
Django signals for vital signs real-time updates
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models_vitals import VitalSign, VitalSignAlert


@receiver(post_save, sender=VitalSign)
def vitals_updated(sender, instance, created, **kwargs):
    """Send real-time update when vitals are created or updated"""
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # Prepare vitals data
        vitals_data = {
            'id': instance.id,
            'systolic_bp': instance.systolic_bp,
            'diastolic_bp': instance.diastolic_bp,
            'blood_pressure_display': instance.blood_pressure_display,
            'heart_rate': instance.heart_rate,
            'temperature': float(instance.temperature) if instance.temperature else None,
            'oxygen_saturation': instance.oxygen_saturation,
            'overall_risk_level': instance.overall_risk_level,
            'bp_category': instance.bp_category,
            'recorded_at': instance.recorded_at.isoformat(),
            'bmi': float(instance.bmi) if instance.bmi else None,
            'recorded_by': instance.recorded_by.get_full_name() if instance.recorded_by else None
        }
        
        # Send to patient's room
        patient_room = f'vitals_patient_{instance.patient.id}'
        async_to_sync(channel_layer.group_send)(
            patient_room,
            {
                'type': 'vitals_update',
                'patient_id': instance.patient.id,
                'data': vitals_data,
                'message': 'New vitals recorded' if created else 'Vitals updated'
            }
        )
        
        # Send to medical staff room
        async_to_sync(channel_layer.group_send)(
            'vitals_medical_staff',
            {
                'type': 'vitals_update',
                'patient_id': instance.patient.id,
                'data': vitals_data,
                'message': f'Vitals {"recorded" if created else "updated"} for {instance.patient.get_full_name()}'
            }
        )


@receiver(post_delete, sender=VitalSign)
def vitals_deleted(sender, instance, **kwargs):
    """Send real-time update when vitals are deleted"""
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # Send to patient's room
        patient_room = f'vitals_patient_{instance.patient.id}'
        async_to_sync(channel_layer.group_send)(
            patient_room,
            {
                'type': 'vitals_deleted',
                'patient_id': instance.patient.id,
                'vital_id': instance.id,
                'message': 'Vitals record deleted'
            }
        )
        
        # Send to medical staff room
        async_to_sync(channel_layer.group_send)(
            'vitals_medical_staff',
            {
                'type': 'vitals_deleted',
                'patient_id': instance.patient.id,
                'vital_id': instance.id,
                'message': f'Vitals record deleted for {instance.patient.get_full_name()}'
            }
        )


@receiver(post_save, sender=VitalSignAlert)
def vitals_alert_created(sender, instance, created, **kwargs):
    """Send real-time alert when vital signs alert is created"""
    if not created:
        return
    
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # Prepare alert data
        alert_data = {
            'id': instance.id,
            'alert_type': instance.alert_type,
            'severity': instance.severity,
            'message': instance.message,
            'patient_name': instance.vital_sign.patient.get_full_name(),
            'patient_id': instance.vital_sign.patient.id,
            'created_at': instance.created_at.isoformat(),
            'vital_sign_id': instance.vital_sign.id,
            'blood_pressure': instance.vital_sign.blood_pressure_display,
            'heart_rate': instance.vital_sign.heart_rate
        }
        
        # Send to alerts room (doctors and admins)
        async_to_sync(channel_layer.group_send)(
            'vitals_alerts',
            {
                'type': 'new_alert',
                'alert_data': alert_data,
                'message': f'Critical vitals alert for {instance.vital_sign.patient.get_full_name()}'
            }
        )
        
        # Send to patient's room
        patient_room = f'vitals_patient_{instance.vital_sign.patient.id}'
        async_to_sync(channel_layer.group_send)(
            patient_room,
            {
                'type': 'vitals_alert',
                'patient_id': instance.vital_sign.patient.id,
                'alert_data': alert_data,
                'message': 'Health alert generated from your vitals'
            }
        )
        
        # Send to medical staff room
        async_to_sync(channel_layer.group_send)(
            'vitals_medical_staff',
            {
                'type': 'vitals_alert',
                'patient_id': instance.vital_sign.patient.id,
                'alert_data': alert_data,
                'message': f'Alert: {instance.get_severity_display()} vitals for {instance.vital_sign.patient.get_full_name()}'
            }
        )


@receiver(post_save, sender=VitalSignAlert)
def vitals_alert_acknowledged(sender, instance, created, **kwargs):
    """Send real-time update when alert is acknowledged"""
    if created or instance.status != 'acknowledged':
        return
    
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # Send to alerts room
        async_to_sync(channel_layer.group_send)(
            'vitals_alerts',
            {
                'type': 'alert_acknowledged',
                'alert_id': instance.id,
                'acknowledged_by': instance.acknowledged_by.get_full_name() if instance.acknowledged_by else None,
                'message': f'Alert acknowledged by {instance.acknowledged_by.get_full_name() if instance.acknowledged_by else "system"}'
            }
        )