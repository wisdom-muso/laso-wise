import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import Consultation, ConsultationMessage, ConsultationParticipant, TechnicalIssue

logger = logging.getLogger(__name__)


class ConsultationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time consultation features
    """
    
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        self.user = self.scope.get('user')
        
        # Check if user is authenticated
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Verify user has access to this consultation
        if not await self.has_consultation_access():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Record participant joining
        await self.record_participant_join()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'user_role': self.user.role,
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Send current consultation status
        await self.send_consultation_status()
    
    async def disconnect(self, close_code):
        # Record participant leaving
        await self.record_participant_leave()
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'consultation_action':
                await self.handle_consultation_action(text_data_json)
            elif message_type == 'technical_issue':
                await self.handle_technical_issue(text_data_json)
            elif message_type == 'connection_quality':
                await self.handle_connection_quality(text_data_json)
            elif message_type == 'typing_indicator':
                await self.handle_typing_indicator(text_data_json)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def handle_chat_message(self, data):
        """Handle chat messages during consultation"""
        message = data.get('message', '').strip()
        is_private = data.get('is_private', False)
        
        if not message:
            return
        
        # Save message to database
        message_obj = await self.save_chat_message(message, is_private)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_obj.id,
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name(),
                'sender_role': self.user.role,
                'is_private': is_private,
                'timestamp': message_obj.timestamp.isoformat(),
            }
        )
    
    async def handle_consultation_action(self, data):
        """Handle consultation state changes (start, end, etc.)"""
        action = data.get('action')
        
        if action == 'start' and self.user.role == 'doctor':
            success = await self.start_consultation()
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'consultation_started',
                        'started_by': self.user.get_full_name(),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
        
        elif action == 'end' and self.user.role == 'doctor':
            success = await self.end_consultation()
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'consultation_ended',
                        'ended_by': self.user.get_full_name(),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
        
        elif action == 'join_waiting_room' and self.user.role == 'patient':
            await self.join_waiting_room()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'patient_waiting',
                    'patient_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_technical_issue(self, data):
        """Handle technical issue reports"""
        issue_type = data.get('issue_type')
        description = data.get('description')
        severity = data.get('severity', 'medium')
        
        if issue_type and description:
            issue = await self.save_technical_issue(issue_type, description, severity)
            
            # Notify all participants about the issue
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'technical_issue_reported',
                    'issue_id': issue.id,
                    'issue_type': issue_type,
                    'description': description,
                    'severity': severity,
                    'reporter': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_connection_quality(self, data):
        """Handle connection quality updates"""
        quality = data.get('quality')
        if quality:
            await self.update_connection_quality(quality)
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicators for chat"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': is_typing,
            }
        )
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        # Only send private messages to medical staff
        if event.get('is_private') and self.user.role not in ['doctor', 'admin']:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_role': event['sender_role'],
            'is_private': event['is_private'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'user_role': event['user_role'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'timestamp': event['timestamp'],
        }))
    
    async def consultation_started(self, event):
        """Send consultation started notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'consultation_started',
            'started_by': event['started_by'],
            'timestamp': event['timestamp'],
        }))
    
    async def consultation_ended(self, event):
        """Send consultation ended notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'consultation_ended',
            'ended_by': event['ended_by'],
            'timestamp': event['timestamp'],
        }))
    
    async def patient_waiting(self, event):
        """Send patient waiting notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'patient_waiting',
            'patient_name': event['patient_name'],
            'timestamp': event['timestamp'],
        }))
    
    async def technical_issue_reported(self, event):
        """Send technical issue notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'technical_issue_reported',
            'issue_id': event['issue_id'],
            'issue_type': event['issue_type'],
            'description': event['description'],
            'severity': event['severity'],
            'reporter': event['reporter'],
            'timestamp': event['timestamp'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def consultation_status_update(self, event):
        """Send consultation status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'consultation_status_update',
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))
    
    # Database operations
    @database_sync_to_async
    def has_consultation_access(self):
        """Check if user has access to this consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return (
                self.user.id == consultation.doctor.id or 
                self.user.id == consultation.patient.id or 
                self.user.role == 'admin'
            )
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_chat_message(self, message, is_private=False):
        """Save chat message to database"""
        consultation = Consultation.objects.get(id=self.consultation_id)
        return ConsultationMessage.objects.create(
            consultation=consultation,
            sender=self.user,
            message=message,
            is_private=is_private
        )
    
    @database_sync_to_async
    def record_participant_join(self):
        """Record participant joining the consultation"""
        consultation = Consultation.objects.get(id=self.consultation_id)
        participant, created = ConsultationParticipant.objects.get_or_create(
            consultation=consultation,
            user=self.user,
            defaults={'role': self.user.role}
        )
        participant.joined_at = timezone.now()
        participant.save()
    
    @database_sync_to_async
    def record_participant_leave(self):
        """Record participant leaving the consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            participant = ConsultationParticipant.objects.get(
                consultation=consultation,
                user=self.user
            )
            participant.left_at = timezone.now()
            participant.save()
        except ConsultationParticipant.DoesNotExist:
            pass
    
    @database_sync_to_async
    def start_consultation(self):
        """Start the consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return consultation.start_consultation()
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def end_consultation(self):
        """End the consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return consultation.end_consultation()
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def join_waiting_room(self):
        """Record patient joining waiting room"""
        from .models import WaitingRoom
        consultation = Consultation.objects.get(id=self.consultation_id)
        waiting_room, created = WaitingRoom.objects.get_or_create(
            consultation=consultation
        )
        if self.user.role == 'patient':
            waiting_room.patient_joined_at = timezone.now()
            waiting_room.save()
    
    @database_sync_to_async
    def save_technical_issue(self, issue_type, description, severity):
        """Save technical issue to database"""
        consultation = Consultation.objects.get(id=self.consultation_id)
        return TechnicalIssue.objects.create(
            consultation=consultation,
            reporter=self.user,
            issue_type=issue_type,
            description=description,
            severity=severity
        )
    
    @database_sync_to_async
    def update_connection_quality(self, quality):
        """Update connection quality for consultation"""
        consultation = Consultation.objects.get(id=self.consultation_id)
        consultation.connection_quality = quality
        consultation.save()
    
    @database_sync_to_async
    def get_consultation_status(self):
        """Get current consultation status"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return {
                'status': consultation.status,
                'can_start': consultation.can_start,
                'is_active': consultation.is_active,
                'scheduled_start': consultation.scheduled_start.isoformat(),
                'actual_start': consultation.actual_start.isoformat() if consultation.actual_start else None,
                'video_provider': consultation.video_provider,
                'meeting_url': consultation.meeting_url,
            }
        except Consultation.DoesNotExist:
            return None
    
    async def send_consultation_status(self):
        """Send current consultation status to user"""
        status = await self.get_consultation_status()
        if status:
            await self.send(text_data=json.dumps({
                'type': 'consultation_status',
                **status
            }))