"""
WebSocket consumers for real-time vital signs updates
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models_vitals import VitalSign, VitalSignAlert

User = get_user_model()


class VitalsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time vital signs updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create room groups based on user type
        if self.user.is_patient():
            # Patients join their own room
            self.room_group_name = f'vitals_patient_{self.user.id}'
        elif self.user.is_doctor() or self.user.is_admin_user():
            # Doctors and admins join a general vitals room
            self.room_group_name = 'vitals_medical_staff'
        else:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to vitals updates',
            'user_type': self.user.user_type
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'subscribe_patient':
                # Doctor/admin subscribing to specific patient updates
                patient_id = text_data_json.get('patient_id')
                if patient_id and (self.user.is_doctor() or self.user.is_admin_user()):
                    await self.subscribe_to_patient(patient_id)
            
            elif message_type == 'request_latest_vitals':
                # Request latest vitals for a patient
                patient_id = text_data_json.get('patient_id')
                if patient_id:
                    await self.send_latest_vitals(patient_id)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def subscribe_to_patient(self, patient_id):
        """Subscribe to a specific patient's vital updates"""
        # Verify permission to access patient data
        has_permission = await self.check_patient_permission(patient_id)
        
        if has_permission:
            patient_room = f'vitals_patient_{patient_id}'
            await self.channel_layer.group_add(
                patient_room,
                self.channel_name
            )
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'patient_id': patient_id,
                'message': f'Subscribed to patient {patient_id} vitals updates'
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Permission denied for patient data'
            }))
    
    async def send_latest_vitals(self, patient_id):
        """Send latest vitals for a patient"""
        has_permission = await self.check_patient_permission(patient_id)
        
        if has_permission:
            vitals_data = await self.get_latest_vitals(patient_id)
            if vitals_data:
                await self.send(text_data=json.dumps({
                    'type': 'latest_vitals',
                    'patient_id': patient_id,
                    'data': vitals_data
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'no_vitals',
                    'patient_id': patient_id,
                    'message': 'No vitals found for this patient'
                }))
    
    @database_sync_to_async
    def check_patient_permission(self, patient_id):
        """Check if user has permission to access patient data"""
        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
            
            if self.user.is_admin_user():
                return True
            elif self.user.is_doctor():
                # Check if doctor has treated this patient
                from appointments.models import Appointment
                return Appointment.objects.filter(
                    doctor=self.user,
                    patient=patient
                ).exists()
            elif self.user.is_patient():
                return self.user.id == int(patient_id)
            
            return False
        except User.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_latest_vitals(self, patient_id):
        """Get latest vitals for a patient"""
        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
            latest_vital = VitalSign.objects.filter(patient=patient).first()
            
            if latest_vital:
                return {
                    'id': latest_vital.id,
                    'systolic_bp': latest_vital.systolic_bp,
                    'diastolic_bp': latest_vital.diastolic_bp,
                    'blood_pressure_display': latest_vital.blood_pressure_display,
                    'heart_rate': latest_vital.heart_rate,
                    'temperature': float(latest_vital.temperature) if latest_vital.temperature else None,
                    'oxygen_saturation': latest_vital.oxygen_saturation,
                    'overall_risk_level': latest_vital.overall_risk_level,
                    'bp_category': latest_vital.bp_category,
                    'recorded_at': latest_vital.recorded_at.isoformat(),
                    'bmi': float(latest_vital.bmi) if latest_vital.bmi else None,
                    'recorded_by': latest_vital.recorded_by.get_full_name() if latest_vital.recorded_by else None
                }
            return None
        except User.DoesNotExist:
            return None
    
    # WebSocket message handlers
    async def vitals_update(self, event):
        """Handle vitals update messages"""
        await self.send(text_data=json.dumps({
            'type': 'vitals_update',
            'patient_id': event['patient_id'],
            'data': event['data'],
            'message': event.get('message', 'Vitals updated')
        }))
    
    async def vitals_alert(self, event):
        """Handle vitals alert messages"""
        await self.send(text_data=json.dumps({
            'type': 'vitals_alert',
            'patient_id': event['patient_id'],
            'alert_data': event['alert_data'],
            'message': event.get('message', 'New vitals alert')
        }))
    
    async def vitals_deleted(self, event):
        """Handle vitals deletion messages"""
        await self.send(text_data=json.dumps({
            'type': 'vitals_deleted',
            'patient_id': event['patient_id'],
            'vital_id': event['vital_id'],
            'message': event.get('message', 'Vitals record deleted')
        }))


class VitalsAlertsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer specifically for vital signs alerts"""
    
    async def connect(self):
        """Handle WebSocket connection for alerts"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Only doctors and admins can receive alerts
        if not (self.user.is_doctor() or self.user.is_admin_user()):
            await self.close()
            return
        
        # Join alerts room
        self.room_group_name = 'vitals_alerts'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send recent unacknowledged alerts
        await self.send_recent_alerts()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'acknowledge_alert':
                alert_id = text_data_json.get('alert_id')
                if alert_id:
                    await self.acknowledge_alert(alert_id)
            
            elif message_type == 'request_alerts':
                await self.send_recent_alerts()
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_recent_alerts(self):
        """Send recent unacknowledged alerts"""
        alerts_data = await self.get_recent_alerts()
        
        await self.send(text_data=json.dumps({
            'type': 'recent_alerts',
            'alerts': alerts_data,
            'count': len(alerts_data)
        }))
    
    @database_sync_to_async
    def get_recent_alerts(self):
        """Get recent unacknowledged alerts"""
        from datetime import datetime, timedelta
        
        # Get alerts from last 24 hours that are still active
        recent_alerts = VitalSignAlert.objects.filter(
            status='active',
            created_at__gte=datetime.now() - timedelta(hours=24)
        ).select_related('vital_sign__patient').order_by('-created_at')[:20]
        
        alerts_data = []
        for alert in recent_alerts:
            alerts_data.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'patient_name': alert.vital_sign.patient.get_full_name(),
                'patient_id': alert.vital_sign.patient.id,
                'created_at': alert.created_at.isoformat(),
                'vital_sign_id': alert.vital_sign.id
            })
        
        return alerts_data
    
    @database_sync_to_async
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert"""
        try:
            alert = VitalSignAlert.objects.get(id=alert_id, status='active')
            alert.status = 'acknowledged'
            alert.acknowledged_by = self.user
            from django.utils import timezone
            alert.acknowledged_at = timezone.now()
            alert.save()
            
            return True
        except VitalSignAlert.DoesNotExist:
            return False
    
    # WebSocket message handlers
    async def new_alert(self, event):
        """Handle new alert messages"""
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert_data'],
            'message': event.get('message', 'New vitals alert')
        }))
    
    async def alert_acknowledged(self, event):
        """Handle alert acknowledgment messages"""
        await self.send(text_data=json.dumps({
            'type': 'alert_acknowledged',
            'alert_id': event['alert_id'],
            'acknowledged_by': event['acknowledged_by'],
            'message': event.get('message', 'Alert acknowledged')
        }))