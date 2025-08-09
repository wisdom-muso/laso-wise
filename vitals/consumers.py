import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import VitalRecord, VitalNotification

User = get_user_model()


class VitalsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time vitals updates
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        # Get user from scope
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create room name based on user
        self.room_name = f"vitals_{self.user.id}"
        self.room_group_name = f"vitals_{self.user.id}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to vitals updates'
        }))
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'subscribe_patient':
                # Subscribe to patient vitals updates
                patient_id = text_data_json.get('patient_id')
                if patient_id and self.user.role in ['doctor', 'admin']:
                    await self.subscribe_to_patient(patient_id)
            
            elif message_type == 'request_vitals_update':
                # Request latest vitals data
                await self.send_vitals_update()
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def subscribe_to_patient(self, patient_id):
        """
        Subscribe to updates for a specific patient
        """
        try:
            patient = await self.get_patient(patient_id)
            if patient:
                # Add to patient's room group
                patient_room = f"vitals_patient_{patient_id}"
                await self.channel_layer.group_add(
                    patient_room,
                    self.channel_name
                )
                
                await self.send(text_data=json.dumps({
                    'type': 'subscription_success',
                    'patient_id': patient_id,
                    'message': f'Subscribed to updates for {patient.get_full_name()}'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'subscription_error',
                'message': str(e)
            }))
    
    async def send_vitals_update(self):
        """
        Send latest vitals data to the client
        """
        try:
            vitals_data = await self.get_latest_vitals()
            await self.send(text_data=json.dumps({
                'type': 'vitals_update',
                'data': vitals_data
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def vitals_update(self, event):
        """
        Handle vitals update event
        """
        await self.send(text_data=json.dumps({
            'type': 'vitals_update',
            'data': event['data']
        }))
    
    async def notification_update(self, event):
        """
        Handle notification update event
        """
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'data': event['data']
        }))
    
    async def alert_update(self, event):
        """
        Handle alert update event
        """
        await self.send(text_data=json.dumps({
            'type': 'alert_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_patient(self, patient_id):
        """
        Get patient by ID
        """
        try:
            return User.objects.get(id=patient_id, role='patient')
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_latest_vitals(self):
        """
        Get latest vitals data for the user
        """
        if self.user.role == 'patient':
            # Get patient's own vitals
            vitals = VitalRecord.objects.filter(
                patient=self.user
            ).select_related('category').order_by('-recorded_at')[:10]
        else:
            # For doctors/admins, get vitals for their patients
            vitals = VitalRecord.objects.filter(
                patient__doctor=self.user
            ).select_related('category', 'patient').order_by('-recorded_at')[:10]
        
        vitals_data = []
        for vital in vitals:
            vitals_data.append({
                'id': vital.id,
                'category': vital.category.name,
                'value': vital.value,
                'secondary_value': vital.secondary_value,
                'status': vital.status,
                'status_display': vital.status_display,
                'recorded_at': vital.recorded_at.isoformat(),
                'patient_name': vital.patient.get_full_name() if self.user.role != 'patient' else None
            })
        
        return vitals_data


class VitalsNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for vitals notifications
    """
    
    async def connect(self):
        """
        Handle WebSocket connection for notifications
        """
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create notification room
        self.room_name = f"notifications_{self.user.id}"
        self.room_group_name = f"notifications_{self.user.id}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread notifications count
        unread_count = await self.get_unread_notifications_count()
        await self.send(text_data=json.dumps({
            'type': 'notifications_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            
            elif message_type == 'get_notifications':
                await self.send_notifications()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def notification_created(self, event):
        """
        Handle new notification event
        """
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_unread_notifications_count(self):
        """
        Get count of unread notifications
        """
        return VitalNotification.objects.filter(
            patient=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark notification as read
        """
        try:
            notification = VitalNotification.objects.get(
                id=notification_id,
                patient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except VitalNotification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_notifications(self):
        """
        Get recent notifications
        """
        notifications = VitalNotification.objects.filter(
            patient=self.user
        ).select_related('vital_record', 'vital_record__category').order_by('-created_at')[:20]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'severity': notification.severity,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'vital_category': notification.vital_record.category.name if notification.vital_record else None
            })
        
        return notifications_data
    
    async def send_notifications(self):
        """
        Send notifications to client
        """
        try:
            notifications = await self.get_notifications()
            await self.send(text_data=json.dumps({
                'type': 'notifications_list',
                'data': notifications
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            })) 