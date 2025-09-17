"""
WebSocket consumers for real-time telemedicine communication
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import TeleMedicineConsultation, TeleMedicineMessage

User = get_user_model()
logger = logging.getLogger(__name__)


class ConsultationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for telemedicine consultations
    Handles WebRTC signaling and real-time chat
    """
    
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        self.user = self.scope['user']
        
        # Verify user can join this consultation
        if await self.can_join_consultation():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Update consultation status
            await self.update_user_joined()
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name(),
                    'user_role': 'doctor' if self.user.is_doctor() else 'patient',
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"User {self.user.id} joined consultation {self.consultation_id}")
        else:
            logger.warning(f"User {self.user.id} denied access to consultation {self.consultation_id}")
            await self.close()

    async def disconnect(self, close_code):
        # Update consultation status
        await self.update_user_left()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"User {self.user.id} left consultation {self.consultation_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route message based on type
            if message_type == 'webrtc_offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'webrtc_answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'ice_candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'screen_share_start':
                await self.handle_screen_share(data)
            elif message_type == 'screen_share_stop':
                await self.handle_screen_share_stop(data)
            elif message_type == 'connection_quality':
                await self.handle_connection_quality(data)
            elif message_type == 'media_state':
                await self.handle_media_state(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    # WebRTC Signaling Handlers
    async def handle_webrtc_offer(self, data):
        """Handle WebRTC offer from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )
        logger.info(f"WebRTC offer sent by user {self.user.id}")

    async def handle_webrtc_answer(self, data):
        """Handle WebRTC answer from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )
        logger.info(f"WebRTC answer sent by user {self.user.id}")

    async def handle_ice_candidate(self, data):
        """Handle ICE candidate from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'ice_candidate',
                'candidate': data['candidate'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_chat_message(self, data):
        """Handle chat message during consultation"""
        message_content = data.get('message', '').strip()
        if not message_content:
            return
            
        # Save message to database
        message_id = await self.save_chat_message(message_content)
        
        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'message': message_content,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_screen_share(self, data):
        """Handle screen sharing start"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_start',
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_screen_share_stop(self, data):
        """Handle screen sharing stop"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_stop',
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_connection_quality(self, data):
        """Handle connection quality updates"""
        quality = data.get('quality', 'unknown')
        await self.update_connection_quality(quality)

    async def handle_media_state(self, data):
        """Handle media state changes (mute/unmute)"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'media_state_change',
                'sender_id': self.user.id,
                'video_enabled': data.get('video_enabled', True),
                'audio_enabled': data.get('audio_enabled', True),
                'timestamp': timezone.now().isoformat()
            }
        )

    # WebSocket message handlers (sent to client)
    async def webrtc_offer(self, event):
        """Send WebRTC offer to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def webrtc_answer(self, event):
        """Send WebRTC answer to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def ice_candidate(self, event):
        """Send ICE candidate to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def chat_message(self, event):
        """Send chat message to client"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'is_own': event['sender_id'] == self.user.id
        }))

    async def user_joined(self, event):
        """Notify client that user joined"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'user_role': event['user_role'],
                'timestamp': event['timestamp']
            }))

    async def user_left(self, event):
        """Notify client that user left"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'timestamp': event['timestamp']
            }))

    async def screen_share_start(self, event):
        """Notify client that screen sharing started"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'screen_share_start',
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))

    async def screen_share_stop(self, event):
        """Notify client that screen sharing stopped"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'screen_share_stop',
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def media_state_change(self, event):
        """Notify client of media state changes"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'media_state_change',
                'sender_id': event['sender_id'],
                'video_enabled': event['video_enabled'],
                'audio_enabled': event['audio_enabled'],
                'timestamp': event['timestamp']
            }))

    # Database operations
    @database_sync_to_async
    def can_join_consultation(self):
        """Check if user can join this consultation"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            return consultation.can_join(self.user)
        except TeleMedicineConsultation.DoesNotExist:
            return False

    @database_sync_to_async
    def update_user_joined(self):
        """Update consultation when user joins"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            
            if self.user.is_doctor():
                consultation.doctor_joined_at = timezone.now()
            else:
                consultation.patient_joined_at = timezone.now()
            
            # Update status if both joined
            if consultation.doctor_joined_at and consultation.patient_joined_at:
                consultation.status = 'in_progress'
                if not consultation.actual_start_time:
                    consultation.actual_start_time = timezone.now()
            
            consultation.save()
            
        except TeleMedicineConsultation.DoesNotExist:
            pass

    @database_sync_to_async
    def update_user_left(self):
        """Update consultation when user leaves"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            
            # If consultation was in progress, mark as completed
            if consultation.status == 'in_progress':
                consultation.end_time = timezone.now()
                consultation.status = 'completed'
                
                # Calculate duration
                if consultation.actual_start_time:
                    duration = consultation.end_time - consultation.actual_start_time
                    consultation.duration_minutes = int(duration.total_seconds() / 60)
                
                consultation.save()
                
        except TeleMedicineConsultation.DoesNotExist:
            pass

    @database_sync_to_async
    def save_chat_message(self, content):
        """Save chat message to database"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            message = TeleMedicineMessage.objects.create(
                consultation=consultation,
                sender=self.user,
                content=content,
                message_type='text'
            )
            return message.id
        except TeleMedicineConsultation.DoesNotExist:
            return None

    @database_sync_to_async
    def update_connection_quality(self, quality):
        """Update connection quality in database"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            consultation.connection_quality = quality
            consultation.save()
        except TeleMedicineConsultation.DoesNotExist:
            pass