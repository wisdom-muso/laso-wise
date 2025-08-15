import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import async_to_sync

from .models import (
    Consultation, ConsultationMessage, ConsultationParticipant, 
    TechnicalIssue, ConsultationSession
)

logger = logging.getLogger(__name__)


class EnhancedConsultationConsumer(AsyncWebsocketConsumer):
    """Enhanced WebSocket consumer for real-time consultation features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consultation_id = None
        self.room_group_name = None
        self.user = None
        self.participant_id = None
        self.session_id = None
        self.heartbeat_task = None
        self.user_status = 'online'
        self.connection_quality = 'good'
        
    async def connect(self):
        """Handle WebSocket connection"""
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        self.user = self.scope.get('user')
        
        # Check if user is authenticated
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        # Verify user has access to this consultation
        if not await self.has_consultation_access():
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Initialize session tracking
        await self.initialize_session()
        
        # Record participant joining
        await self.record_participant_join()
        
        # Notify others that user joined
        await self.broadcast_user_status('joined')
        
        # Send current consultation state
        await self.send_consultation_state()
        
        # Start heartbeat monitoring
        self.heartbeat_task = asyncio.create_task(self.heartbeat_monitor())
        
        logger.info(f"User {self.user.id} connected to consultation {self.consultation_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Cancel heartbeat monitoring
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Record participant leaving
        await self.record_participant_leave()
        
        # Notify others that user left
        await self.broadcast_user_status('left')
        
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Update session end time
        await self.end_session()
        
        logger.info(f"User {self.user.id} disconnected from consultation {self.consultation_id}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route message to appropriate handler
            handler_map = {
                'chat_message': self.handle_chat_message,
                'typing_indicator': self.handle_typing_indicator,
                'status_update': self.handle_status_update,
                'quality_update': self.handle_quality_update,
                'screen_share': self.handle_screen_share,
                'file_share': self.handle_file_share,
                'technical_issue': self.handle_technical_issue,
                'consultation_control': self.handle_consultation_control,
                'participant_action': self.handle_participant_action,
                'heartbeat': self.handle_heartbeat,
                'cursor_position': self.handle_cursor_position,
                'annotation': self.handle_annotation,
            }
            
            handler = handler_map.get(message_type)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error("Message processing failed")
    
    async def handle_chat_message(self, data: Dict[str, Any]):
        """Handle chat messages"""
        message_content = data.get('message', '').strip()
        is_private = data.get('is_private', False)
        message_type = data.get('message_type', 'text')
        
        if not message_content:
            await self.send_error("Message content is required")
            return
        
        # Save message to database
        message = await self.save_message(
            message_content, 
            message_type, 
            is_private
        )
        
        if message:
            # Broadcast message to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': {
                        'id': message.id,
                        'content': message_content,
                        'message_type': message_type,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name(),
                        'sender_role': self.user.role,
                        'timestamp': message.timestamp.isoformat(),
                        'is_private': is_private,
                    }
                }
            )
    
    async def handle_typing_indicator(self, data: Dict[str, Any]):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': is_typing,
            }
        )
    
    async def handle_status_update(self, data: Dict[str, Any]):
        """Handle user status updates"""
        status = data.get('status', 'online')
        self.user_status = status
        
        # Update participant status in cache
        await self.update_participant_cache('status', status)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_update_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'status': status,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_quality_update(self, data: Dict[str, Any]):
        """Handle connection quality updates"""
        quality = data.get('quality', 'good')
        self.connection_quality = quality
        
        # Update consultation quality
        await self.update_consultation_quality(quality)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quality_update_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'quality': quality,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_screen_share(self, data: Dict[str, Any]):
        """Handle screen sharing events"""
        action = data.get('action', 'start')  # start, stop, request
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'action': action,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_file_share(self, data: Dict[str, Any]):
        """Handle file sharing"""
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        file_type = data.get('file_type')
        file_url = data.get('file_url')
        
        if not all([file_name, file_url]):
            await self.send_error("File name and URL are required")
            return
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_share_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'file_name': file_name,
                'file_size': file_size,
                'file_type': file_type,
                'file_url': file_url,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_technical_issue(self, data: Dict[str, Any]):
        """Handle technical issue reports"""
        issue_type = data.get('issue_type')
        description = data.get('description')
        severity = data.get('severity', 'medium')
        
        if not all([issue_type, description]):
            await self.send_error("Issue type and description are required")
            return
        
        # Save technical issue to database
        issue = await self.save_technical_issue(issue_type, description, severity)
        
        if issue:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'technical_issue_broadcast',
                    'issue_id': str(issue.id),
                    'reporter_id': self.user.id,
                    'reporter_name': self.user.get_full_name(),
                    'issue_type': issue_type,
                    'description': description,
                    'severity': severity,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_consultation_control(self, data: Dict[str, Any]):
        """Handle consultation control actions (start, end, pause)"""
        action = data.get('action')
        
        if action not in ['start', 'end', 'pause', 'resume']:
            await self.send_error("Invalid consultation action")
            return
        
        # Only doctor can control consultation
        if self.user.role != 'doctor':
            await self.send_error("Only doctors can control consultations")
            return
        
        success = await self.update_consultation_status(action)
        
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'consultation_control_broadcast',
                    'action': action,
                    'controller_id': self.user.id,
                    'controller_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_participant_action(self, data: Dict[str, Any]):
        """Handle participant-specific actions (mute, video toggle, etc.)"""
        action = data.get('action')
        target_user_id = data.get('target_user_id')
        
        # Record participant action
        await self.update_participant_cache('last_action', {
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'data': data
        })
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_action_broadcast',
                'action': action,
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'target_user_id': target_user_id,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_heartbeat(self, data: Dict[str, Any]):
        """Handle heartbeat messages"""
        await self.update_participant_cache('last_heartbeat', timezone.now().isoformat())
        
        # Send heartbeat response
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def handle_cursor_position(self, data: Dict[str, Any]):
        """Handle cursor position sharing (for screen sharing)"""
        x = data.get('x')
        y = data.get('y')
        
        if x is not None and y is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cursor_position_broadcast',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name(),
                    'x': x,
                    'y': y,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_annotation(self, data: Dict[str, Any]):
        """Handle screen annotations during sharing"""
        annotation_type = data.get('annotation_type', 'highlight')
        coordinates = data.get('coordinates', {})
        color = data.get('color', '#ff0000')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'annotation_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'annotation_type': annotation_type,
                'coordinates': coordinates,
                'color': color,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    # Broadcast handlers
    async def chat_message_broadcast(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator_broadcast(self, event):
        """Send typing indicator to WebSocket"""
        if event['user_id'] != self.user.id:  # Don't send to sender
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def status_update_broadcast(self, event):
        """Send status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))
    
    async def quality_update_broadcast(self, event):
        """Send quality update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'quality_update',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'quality': event['quality'],
            'timestamp': event['timestamp'],
        }))
    
    async def screen_share_broadcast(self, event):
        """Send screen sharing event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'screen_share',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'action': event['action'],
            'timestamp': event['timestamp'],
        }))
    
    async def file_share_broadcast(self, event):
        """Send file sharing event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'file_share',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'file_name': event['file_name'],
            'file_size': event['file_size'],
            'file_type': event['file_type'],
            'file_url': event['file_url'],
            'timestamp': event['timestamp'],
        }))
    
    async def technical_issue_broadcast(self, event):
        """Send technical issue to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'technical_issue',
            'issue_id': event['issue_id'],
            'reporter_id': event['reporter_id'],
            'reporter_name': event['reporter_name'],
            'issue_type': event['issue_type'],
            'description': event['description'],
            'severity': event['severity'],
            'timestamp': event['timestamp'],
        }))
    
    async def consultation_control_broadcast(self, event):
        """Send consultation control event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'consultation_control',
            'action': event['action'],
            'controller_id': event['controller_id'],
            'controller_name': event['controller_name'],
            'timestamp': event['timestamp'],
        }))
    
    async def participant_action_broadcast(self, event):
        """Send participant action to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'participant_action',
            'action': event['action'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'target_user_id': event.get('target_user_id'),
            'timestamp': event['timestamp'],
        }))
    
    async def cursor_position_broadcast(self, event):
        """Send cursor position to WebSocket"""
        if event['user_id'] != self.user.id:  # Don't send to sender
            await self.send(text_data=json.dumps({
                'type': 'cursor_position',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'x': event['x'],
                'y': event['y'],
                'timestamp': event['timestamp'],
            }))
    
    async def annotation_broadcast(self, event):
        """Send annotation to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'annotation',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'annotation_type': event['annotation_type'],
            'coordinates': event['coordinates'],
            'color': event['color'],
            'timestamp': event['timestamp'],
        }))
    
    # Helper methods
    async def send_error(self, message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def heartbeat_monitor(self):
        """Monitor connection health with heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_ping',
                    'timestamp': timezone.now().isoformat(),
                }))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def broadcast_user_status(self, status: str):
        """Broadcast user join/leave status"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status_broadcast',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'user_role': self.user.role,
                'status': status,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def user_status_broadcast(self, event):
        """Send user status to WebSocket"""
        if event['user_id'] != self.user.id:  # Don't send to sender
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'user_role': event['user_role'],
                'status': event['status'],
                'timestamp': event['timestamp'],
            }))
    
    async def send_consultation_state(self):
        """Send current consultation state to newly connected user"""
        consultation = await self.get_consultation()
        if consultation:
            participants = await self.get_active_participants()
            recent_messages = await self.get_recent_messages()
            
            await self.send(text_data=json.dumps({
                'type': 'consultation_state',
                'consultation': {
                    'id': str(consultation.id),
                    'status': consultation.status,
                    'scheduled_start': consultation.scheduled_start.isoformat(),
                    'actual_start': consultation.actual_start.isoformat() if consultation.actual_start else None,
                    'video_provider': consultation.video_provider,
                },
                'participants': participants,
                'recent_messages': recent_messages,
                'timestamp': timezone.now().isoformat(),
            }))
    
    # Database operations
    @database_sync_to_async
    def has_consultation_access(self) -> bool:
        """Check if user has access to this consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return (
                self.user == consultation.doctor or 
                self.user == consultation.patient or
                self.user.role == 'admin'
            )
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_consultation(self):
        """Get consultation object"""
        try:
            return Consultation.objects.get(id=self.consultation_id)
        except Consultation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, content: str, message_type: str, is_private: bool):
        """Save chat message to database"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            message = ConsultationMessage.objects.create(
                consultation=consultation,
                sender=self.user,
                message=content,
                message_type=message_type,
                is_private=is_private
            )
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def save_technical_issue(self, issue_type: str, description: str, severity: str):
        """Save technical issue to database"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            issue = TechnicalIssue.objects.create(
                consultation=consultation,
                reporter=self.user,
                issue_type=issue_type,
                description=description,
                severity=severity
            )
            return issue
        except Exception as e:
            logger.error(f"Error saving technical issue: {e}")
            return None
    
    @database_sync_to_async
    def record_participant_join(self):
        """Record participant joining consultation"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            participant, created = ConsultationParticipant.objects.get_or_create(
                consultation=consultation,
                user=self.user,
                defaults={'role': self.user.role}
            )
            participant.joined_at = timezone.now()
            participant.save()
            self.participant_id = participant.id
        except Exception as e:
            logger.error(f"Error recording participant join: {e}")
    
    @database_sync_to_async
    def record_participant_leave(self):
        """Record participant leaving consultation"""
        try:
            if self.participant_id:
                participant = ConsultationParticipant.objects.get(id=self.participant_id)
                participant.left_at = timezone.now()
                if participant.joined_at:
                    duration = timezone.now() - participant.joined_at
                    participant.total_duration_seconds = int(duration.total_seconds())
                participant.save()
        except Exception as e:
            logger.error(f"Error recording participant leave: {e}")
    
    @database_sync_to_async
    def update_consultation_status(self, action: str) -> bool:
        """Update consultation status based on action"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            
            if action == 'start' and consultation.can_start:
                consultation.start_consultation()
                return True
            elif action == 'end' and consultation.status == 'in_progress':
                consultation.end_consultation()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating consultation status: {e}")
            return False
    
    @database_sync_to_async
    def update_consultation_quality(self, quality: str):
        """Update consultation connection quality"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            consultation.connection_quality = quality
            consultation.save()
        except Exception as e:
            logger.error(f"Error updating consultation quality: {e}")
    
    @database_sync_to_async
    def get_active_participants(self) -> List[Dict[str, Any]]:
        """Get list of active participants"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            participants = ConsultationParticipant.objects.filter(
                consultation=consultation,
                left_at__isnull=True
            ).select_related('user')
            
            return [
                {
                    'id': p.user.id,
                    'name': p.user.get_full_name(),
                    'role': p.role,
                    'joined_at': p.joined_at.isoformat() if p.joined_at else None,
                }
                for p in participants
            ]
        except Exception as e:
            logger.error(f"Error getting active participants: {e}")
            return []
    
    @database_sync_to_async
    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent chat messages"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            messages = ConsultationMessage.objects.filter(
                consultation=consultation
            ).order_by('-timestamp')[:limit]
            
            return [
                {
                    'id': m.id,
                    'content': m.message,
                    'message_type': m.message_type,
                    'sender_id': m.sender.id,
                    'sender_name': m.sender.get_full_name(),
                    'sender_role': m.sender.role,
                    'timestamp': m.timestamp.isoformat(),
                    'is_private': m.is_private,
                }
                for m in reversed(messages)
            ]
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []
    
    async def initialize_session(self):
        """Initialize consultation session tracking"""
        try:
            # Create or get session
            session_data = await self.create_session()
            self.session_id = session_data['session_id']
            
            # Store participant data in cache
            await self.update_participant_cache('connected_at', timezone.now().isoformat())
            
        except Exception as e:
            logger.error(f"Error initializing session: {e}")
    
    async def end_session(self):
        """End consultation session"""
        try:
            if self.session_id:
                await self.update_session_end()
            
            # Clean up participant cache
            await self.cleanup_participant_cache()
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    @database_sync_to_async
    def create_session(self) -> Dict[str, Any]:
        """Create consultation session"""
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            session = ConsultationSession.objects.create(
                consultation=consultation
            )
            return {
                'session_id': str(session.session_id),
                'started_at': session.started_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {}
    
    @database_sync_to_async
    def update_session_end(self):
        """Update session end time"""
        try:
            session = ConsultationSession.objects.get(session_id=self.session_id)
            session.ended_at = timezone.now()
            if session.started_at:
                duration = timezone.now() - session.started_at
                session.duration_seconds = int(duration.total_seconds())
            session.save()
        except Exception as e:
            logger.error(f"Error updating session end: {e}")
    
    async def update_participant_cache(self, key: str, value: Any):
        """Update participant data in cache"""
        cache_key = f"consultation_{self.consultation_id}_participant_{self.user.id}"
        participant_data = cache.get(cache_key, {})
        participant_data[key] = value
        cache.set(cache_key, participant_data, timeout=3600)  # 1 hour
    
    async def cleanup_participant_cache(self):
        """Clean up participant cache data"""
        cache_key = f"consultation_{self.consultation_id}_participant_{self.user.id}"
        cache.delete(cache_key)