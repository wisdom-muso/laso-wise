import json
import jwt
import requests
from datetime import datetime, timedelta
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)


class VideoProviderService:
    """Base class for video provider services"""
    
    def create_meeting(self, consultation):
        """Create a meeting for the consultation"""
        raise NotImplementedError
    
    def get_meeting_info(self, meeting_id):
        """Get meeting information"""
        raise NotImplementedError
    
    def delete_meeting(self, meeting_id):
        """Delete a meeting"""
        raise NotImplementedError
    
    def get_recording_info(self, meeting_id):
        """Get recording information"""
        raise NotImplementedError


class JitsiService(VideoProviderService):
    """Service for Jitsi Meet integration"""
    
    def __init__(self):
        self.domain = settings.TELEMEDICINE_CONFIG.get('JITSI_DOMAIN', 'meet.jit.si')
    
    def create_meeting(self, consultation):
        """Create a Jitsi meeting room"""
        room_name = f"laso-consultation-{consultation.id}"
        meeting_url = f"https://{self.domain}/{room_name}"
        
        # Generate room password for security
        password = self._generate_room_password()
        
        consultation.meeting_id = room_name
        consultation.meeting_url = meeting_url
        consultation.meeting_password = password
        consultation.save()
        
        return {
            'meeting_id': room_name,
            'meeting_url': meeting_url,
            'password': password,
            'join_url': f"{meeting_url}#{password}",
            'provider': 'jitsi'
        }
    
    def get_meeting_info(self, meeting_id):
        """Get Jitsi meeting info (basic implementation)"""
        return {
            'meeting_id': meeting_id,
            'meeting_url': f"https://{self.domain}/{meeting_id}",
            'status': 'active',
            'provider': 'jitsi'
        }
    
    def delete_meeting(self, meeting_id):
        """Jitsi rooms don't need explicit deletion"""
        return True
    
    def get_recording_info(self, meeting_id):
        """Jitsi recordings are handled differently"""
        return None
    
    def _generate_room_password(self):
        """Generate a secure room password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))


class ZoomService(VideoProviderService):
    """Service for Zoom integration"""
    
    def __init__(self):
        self.api_key = settings.TELEMEDICINE_CONFIG.get('ZOOM_API_KEY')
        self.api_secret = settings.TELEMEDICINE_CONFIG.get('ZOOM_API_SECRET')
        self.base_url = 'https://api.zoom.us/v2'
    
    def _get_jwt_token(self):
        """Generate JWT token for Zoom API authentication"""
        if not self.api_key or not self.api_secret:
            raise ValueError("Zoom API credentials not configured")
        
        payload = {
            'iss': self.api_key,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.api_secret, algorithm='HS256')
    
    def _make_request(self, method, endpoint, data=None):
        """Make authenticated request to Zoom API"""
        headers = {
            'Authorization': f'Bearer {self._get_jwt_token()}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom API request failed: {e}")
            raise
    
    def create_meeting(self, consultation):
        """Create a Zoom meeting"""
        meeting_data = {
            'topic': f"Consultation: Dr. {consultation.doctor.get_full_name()} with {consultation.patient.get_full_name()}",
            'type': 2,  # Scheduled meeting
            'start_time': consultation.scheduled_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'duration': 60,  # Default 60 minutes
            'timezone': 'UTC',
            'settings': {
                'host_video': True,
                'participant_video': True,
                'cn_meeting': False,
                'in_meeting': False,
                'join_before_host': False,
                'mute_upon_entry': True,
                'watermark': False,
                'use_pmi': False,
                'approval_type': 0,  # Automatically approve
                'registration_type': 1,
                'audio': 'both',
                'auto_recording': 'cloud' if settings.TELEMEDICINE_CONFIG.get('RECORDING_ENABLED') else 'none',
                'waiting_room': True,
            }
        }
        
        # Use the doctor's email as the host (you may need to adjust this)
        user_id = consultation.doctor.email
        response = self._make_request('POST', f'/users/{user_id}/meetings', meeting_data)
        
        consultation.meeting_id = str(response['id'])
        consultation.meeting_url = response['join_url']
        consultation.meeting_password = response.get('password', '')
        consultation.save()
        
        return {
            'meeting_id': response['id'],
            'meeting_url': response['join_url'],
            'password': response.get('password', ''),
            'start_url': response['start_url'],
            'provider': 'zoom'
        }
    
    def get_meeting_info(self, meeting_id):
        """Get Zoom meeting information"""
        response = self._make_request('GET', f'/meetings/{meeting_id}')
        return {
            'meeting_id': response['id'],
            'meeting_url': response['join_url'],
            'status': response['status'],
            'start_time': response.get('start_time'),
            'duration': response.get('duration'),
            'provider': 'zoom'
        }
    
    def delete_meeting(self, meeting_id):
        """Delete a Zoom meeting"""
        try:
            self._make_request('DELETE', f'/meetings/{meeting_id}')
            return True
        except Exception as e:
            logger.error(f"Failed to delete Zoom meeting {meeting_id}: {e}")
            return False
    
    def get_recording_info(self, meeting_id):
        """Get Zoom recording information"""
        try:
            response = self._make_request('GET', f'/meetings/{meeting_id}/recordings')
            return response
        except Exception as e:
            logger.error(f"Failed to get Zoom recording for meeting {meeting_id}: {e}")
            return None


class GoogleMeetService(VideoProviderService):
    """Service for Google Meet integration"""
    
    def __init__(self):
        self.client_id = settings.TELEMEDICINE_CONFIG.get('GOOGLE_MEET_CLIENT_ID')
        self.client_secret = settings.TELEMEDICINE_CONFIG.get('GOOGLE_MEET_CLIENT_SECRET')
        
        # Note: Google Meet integration requires OAuth2 flow and Calendar API
        # This is a simplified implementation
    
    def create_meeting(self, consultation):
        """Create a Google Meet meeting via Calendar API"""
        # This would require proper OAuth2 setup and Calendar API access
        # For now, we'll create a basic meeting URL
        
        meeting_id = f"meet-{consultation.id}"
        meeting_url = f"https://meet.google.com/{meeting_id}"
        
        consultation.meeting_id = meeting_id
        consultation.meeting_url = meeting_url
        consultation.save()
        
        return {
            'meeting_id': meeting_id,
            'meeting_url': meeting_url,
            'provider': 'google_meet'
        }
    
    def get_meeting_info(self, meeting_id):
        """Get Google Meet meeting info"""
        return {
            'meeting_id': meeting_id,
            'meeting_url': f"https://meet.google.com/{meeting_id}",
            'status': 'active',
            'provider': 'google_meet'
        }
    
    def delete_meeting(self, meeting_id):
        """Delete Google Meet meeting"""
        # Would require Calendar API integration
        return True
    
    def get_recording_info(self, meeting_id):
        """Get Google Meet recording info"""
        # Google Meet recordings are stored in Google Drive
        return None


class VideoProviderFactory:
    """Factory for creating video provider services"""
    
    @staticmethod
    def get_service(provider):
        """Get the appropriate video provider service"""
        if provider == 'jitsi':
            return JitsiService()
        elif provider == 'zoom':
            return ZoomService()
        elif provider == 'google_meet':
            return GoogleMeetService()
        else:
            raise ValueError(f"Unsupported video provider: {provider}")


class ConsultationService:
    """Service for managing consultations and video meetings"""
    
    def create_consultation_with_meeting(self, booking, video_provider='jitsi', **kwargs):
        """Create consultation and associated video meeting"""
        from .models import Consultation
        from django.utils import timezone
        
        # Create consultation
        consultation = Consultation.objects.create(
            booking=booking,
            doctor=booking.doctor,
            patient=booking.patient,
            video_provider=video_provider,
            scheduled_start=timezone.datetime.combine(
                booking.appointment_date,
                booking.appointment_time,
                timezone.get_current_timezone()
            ),
            **kwargs
        )
        
        # Create video meeting
        video_service = VideoProviderFactory.get_service(video_provider)
        meeting_info = video_service.create_meeting(consultation)
        
        return consultation, meeting_info
    
    def start_consultation(self, consultation):
        """Start a consultation"""
        if consultation.can_start:
            consultation.start_consultation()
            
            # Send notifications via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'consultation_{consultation.id}',
                {
                    'type': 'consultation_started',
                    'consultation_id': str(consultation.id),
                    'started_by': consultation.doctor.get_full_name(),
                    'timestamp': consultation.actual_start.isoformat(),
                }
            )
            
            return True
        return False
    
    def end_consultation(self, consultation, notes=None):
        """End a consultation"""
        if consultation.status == 'in_progress':
            consultation.end_consultation()
            
            if notes:
                consultation.notes = notes
                consultation.save()
            
            # Send notifications via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'consultation_{consultation.id}',
                {
                    'type': 'consultation_ended',
                    'consultation_id': str(consultation.id),
                    'ended_by': consultation.doctor.get_full_name(),
                    'timestamp': consultation.actual_end.isoformat(),
                    'duration_minutes': consultation.duration_minutes,
                }
            )
            
            return True
        return False
    
    def get_consultation_stats(self, user):
        """Get consultation statistics for a user"""
        from .models import Consultation, ConsultationStatus
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        
        # Filter consultations based on user role
        if user.role == 'doctor':
            queryset = Consultation.objects.filter(doctor=user)
        elif user.role == 'patient':
            queryset = Consultation.objects.filter(patient=user)
        else:
            queryset = Consultation.objects.none()
        
        total = queryset.count()
        completed = queryset.filter(status=ConsultationStatus.COMPLETED).count()
        upcoming = queryset.filter(
            scheduled_start__gte=timezone.now(),
            status__in=[ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING]
        ).count()
        active = queryset.filter(
            status__in=[ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]
        ).count()
        
        # Calculate average duration
        avg_duration = queryset.filter(
            status=ConsultationStatus.COMPLETED,
            duration_minutes__isnull=False
        ).aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
        
        return {
            'total_consultations': total,
            'completed_consultations': completed,
            'upcoming_consultations': upcoming,
            'active_consultations': active,
            'average_duration': round(avg_duration, 2),
        }