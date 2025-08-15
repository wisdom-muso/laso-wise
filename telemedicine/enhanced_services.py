import json
import jwt
import requests
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)


class VideoProviderError(Exception):
    """Custom exception for video provider errors"""
    pass


class BaseVideoProvider:
    """Enhanced base class for video provider services"""
    
    def __init__(self):
        self.provider_name = None
        self.cache_timeout = 300  # 5 minutes
    
    def create_meeting(self, consultation) -> Dict[str, Any]:
        """Create a meeting for the consultation"""
        raise NotImplementedError
    
    def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        """Get meeting information"""
        raise NotImplementedError
    
    def update_meeting(self, meeting_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update meeting settings"""
        raise NotImplementedError
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting"""
        raise NotImplementedError
    
    def get_recording_info(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get recording information"""
        raise NotImplementedError
    
    def start_recording(self, meeting_id: str) -> bool:
        """Start recording (if supported)"""
        return False
    
    def stop_recording(self, meeting_id: str) -> bool:
        """Stop recording (if supported)"""
        return False
    
    def validate_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Validate webhook signature"""
        return True
    
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook from provider"""
        return {}
    
    def get_participant_count(self, meeting_id: str) -> int:
        """Get current participant count"""
        return 0
    
    def mute_participant(self, meeting_id: str, participant_id: str) -> bool:
        """Mute a participant"""
        return False
    
    def remove_participant(self, meeting_id: str, participant_id: str) -> bool:
        """Remove a participant"""
        return False


class EnhancedJitsiService(BaseVideoProvider):
    """Enhanced Jitsi Meet integration with additional features"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = 'jitsi'
        self.domain = settings.TELEMEDICINE_CONFIG.get('JITSI_DOMAIN', 'meet.jit.si')
        self.jwt_secret = settings.TELEMEDICINE_CONFIG.get('JITSI_JWT_SECRET', '')
        self.jwt_app_id = settings.TELEMEDICINE_CONFIG.get('JITSI_JWT_APP_ID', '')
    
    def create_meeting(self, consultation) -> Dict[str, Any]:
        """Create a Jitsi meeting room with JWT authentication"""
        room_name = f"laso-consultation-{consultation.id}"
        password = self._generate_secure_password()
        
        # Create JWT token for room access
        jwt_token = self._create_jwt_token(room_name, consultation)
        
        meeting_url = f"https://{self.domain}/{room_name}"
        if jwt_token:
            meeting_url += f"?jwt={jwt_token}"
        
        consultation.meeting_id = room_name
        consultation.meeting_url = meeting_url
        consultation.meeting_password = password
        consultation.save()
        
        # Store meeting info in cache
        cache_key = f"jitsi_meeting_{room_name}"
        meeting_data = {
            'room_name': room_name,
            'consultation_id': str(consultation.id),
            'created_at': timezone.now().isoformat(),
            'password': password,
            'jwt_token': jwt_token,
        }
        cache.set(cache_key, meeting_data, self.cache_timeout)
        
        return {
            'meeting_id': room_name,
            'meeting_url': meeting_url,
            'password': password,
            'join_url': meeting_url,
            'provider': self.provider_name,
            'jwt_token': jwt_token,
            'room_config': self._get_room_config(consultation)
        }
    
    def _create_jwt_token(self, room_name: str, consultation) -> Optional[str]:
        """Create JWT token for Jitsi room authentication"""
        if not self.jwt_secret or not self.jwt_app_id:
            return None
        
        payload = {
            'iss': self.jwt_app_id,
            'aud': self.jwt_app_id,
            'exp': int((timezone.now() + timedelta(hours=24)).timestamp()),
            'room': room_name,
            'context': {
                'user': {
                    'name': consultation.doctor.get_full_name(),
                    'email': consultation.doctor.email,
                    'avatar': getattr(consultation.doctor.profile, 'avatar', ''),
                },
                'group': consultation.id,
            },
            'moderator': True,
        }
        
        try:
            return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            return None
    
    def _get_room_config(self, consultation) -> Dict[str, Any]:
        """Get Jitsi room configuration"""
        return {
            'enableWelcomePage': False,
            'prejoinPageEnabled': True,
            'requireDisplayName': True,
            'disableModeratorIndicator': False,
            'startWithAudioMuted': True,
            'startWithVideoMuted': False,
            'enableUserRolesBasedOnToken': True,
            'enableFeaturesBasedOnToken': True,
            'recordingEnabled': consultation.recording_enabled,
            'liveStreamingEnabled': False,
            'resolution': 720,
            'constraints': {
                'video': {
                    'height': {'ideal': 720, 'max': 1080, 'min': 240}
                }
            }
        }
    
    def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        """Get Jitsi meeting info from cache or create basic info"""
        cache_key = f"jitsi_meeting_{meeting_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return {
                'meeting_id': meeting_id,
                'meeting_url': f"https://{self.domain}/{meeting_id}",
                'status': 'active',
                'provider': self.provider_name,
                'created_at': cached_data.get('created_at'),
                'participant_count': self.get_participant_count(meeting_id)
            }
        
        return {
            'meeting_id': meeting_id,
            'meeting_url': f"https://{self.domain}/{meeting_id}",
            'status': 'unknown',
            'provider': self.provider_name
        }
    
    def _generate_secure_password(self) -> str:
        """Generate a secure room password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(12))


class EnhancedZoomService(BaseVideoProvider):
    """Enhanced Zoom integration with OAuth2 and webhooks"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = 'zoom'
        self.api_key = settings.TELEMEDICINE_CONFIG.get('ZOOM_API_KEY')
        self.api_secret = settings.TELEMEDICINE_CONFIG.get('ZOOM_API_SECRET')
        self.webhook_secret = settings.TELEMEDICINE_CONFIG.get('ZOOM_WEBHOOK_SECRET', '')
        self.base_url = 'https://api.zoom.us/v2'
        self.oauth_url = 'https://zoom.us/oauth'
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token for Zoom API"""
        cache_key = 'zoom_access_token'
        token = cache.get(cache_key)
        
        if not token:
            token = self._refresh_access_token()
            if token:
                # Cache token for 50 minutes (expires in 1 hour)
                cache.set(cache_key, token, 3000)
        
        return token
    
    def _refresh_access_token(self) -> Optional[str]:
        """Refresh OAuth2 access token"""
        if not self.api_key or not self.api_secret:
            raise VideoProviderError("Zoom API credentials not configured")
        
        import base64
        
        # Encode credentials
        credentials = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        try:
            response = requests.post(f"{self.oauth_url}/token", headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get('access_token')
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Zoom access token: {e}")
            raise VideoProviderError(f"Zoom authentication failed: {e}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Zoom API"""
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom API request failed: {e}")
            if response.status_code == 401:
                # Token expired, clear cache and retry once
                cache.delete('zoom_access_token')
                if not hasattr(self, '_retry_attempted'):
                    self._retry_attempted = True
                    return self._make_request(method, endpoint, data)
            raise VideoProviderError(f"Zoom API error: {e}")
    
    def create_meeting(self, consultation) -> Dict[str, Any]:
        """Create an advanced Zoom meeting"""
        meeting_data = {
            'topic': f"Medical Consultation: Dr. {consultation.doctor.get_full_name()} with {consultation.patient.get_full_name()}",
            'type': 2,  # Scheduled meeting
            'start_time': consultation.scheduled_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'duration': getattr(consultation, 'expected_duration', 60),
            'timezone': 'UTC',
            'agenda': f"Virtual medical consultation for {consultation.patient.get_full_name()}",
            'settings': {
                'host_video': True,
                'participant_video': True,
                'cn_meeting': False,
                'in_meeting': False,
                'join_before_host': True,
                'jbh_time': 5,  # 5 minutes before host
                'mute_upon_entry': True,
                'watermark': True,
                'use_pmi': False,
                'approval_type': 0,  # Automatically approve
                'registration_type': 1,
                'audio': 'both',
                'auto_recording': 'cloud' if consultation.recording_enabled else 'none',
                'enforce_login': False,
                'enforce_login_domains': '',
                'alternative_hosts': '',
                'close_registration': False,
                'show_share_button': True,
                'allow_multiple_devices': True,
                'waiting_room': True,
                'request_permission_to_unmute_participants': True,
                'global_dial_in_countries': ['US'],
                'contact_name': consultation.doctor.get_full_name(),
                'contact_email': consultation.doctor.email,
                'registrants_confirmation_email': True,
                'registrants_email_notification': True,
                'meeting_authentication': False,
                'encryption_type': 'enhanced_encryption',
                'approved_or_denied_countries_or_regions': {
                    'enable': False
                }
            }
        }
        
        user_id = consultation.doctor.email
        response = self._make_request('POST', f'/users/{user_id}/meetings', meeting_data)
        
        consultation.meeting_id = str(response['id'])
        consultation.meeting_url = response['join_url']
        consultation.meeting_password = response.get('password', '')
        consultation.save()
        
        # Store additional meeting data
        cache_key = f"zoom_meeting_{response['id']}"
        cache.set(cache_key, {
            'consultation_id': str(consultation.id),
            'host_id': response.get('host_id'),
            'start_url': response.get('start_url'),
            'created_at': timezone.now().isoformat(),
        }, self.cache_timeout)
        
        return {
            'meeting_id': response['id'],
            'meeting_url': response['join_url'],
            'password': response.get('password', ''),
            'start_url': response['start_url'],
            'provider': self.provider_name,
            'host_id': response.get('host_id'),
            'registration_url': response.get('registration_url'),
        }
    
    def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        """Get comprehensive Zoom meeting information"""
        try:
            response = self._make_request('GET', f'/meetings/{meeting_id}')
            
            # Get live meeting info if active
            live_info = {}
            try:
                live_response = self._make_request('GET', f'/metrics/meetings/{meeting_id}')
                live_info = {
                    'participant_count': len(live_response.get('participants', [])),
                    'start_time': live_response.get('start_time'),
                    'end_time': live_response.get('end_time'),
                }
            except:
                pass
            
            return {
                'meeting_id': response['id'],
                'meeting_url': response['join_url'],
                'status': response['status'],
                'start_time': response.get('start_time'),
                'duration': response.get('duration'),
                'provider': self.provider_name,
                'topic': response.get('topic'),
                'password': response.get('password'),
                'waiting_room': response.get('settings', {}).get('waiting_room'),
                **live_info
            }
        except Exception as e:
            logger.error(f"Failed to get Zoom meeting info: {e}")
            return {'error': str(e)}
    
    def validate_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Validate Zoom webhook signature"""
        if not self.webhook_secret:
            return True  # Skip validation if no secret configured
        
        import hmac
        import hashlib
        
        message = json.dumps(payload, separators=(',', ':')).encode()
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Zoom webhook events"""
        event_type = payload.get('event')
        meeting_id = payload.get('payload', {}).get('object', {}).get('id')
        
        if not meeting_id:
            return {'error': 'No meeting ID in webhook'}
        
        # Update consultation based on event
        try:
            from .models import Consultation
            consultation = Consultation.objects.get(meeting_id=str(meeting_id))
            
            if event_type == 'meeting.started':
                consultation.actual_start = timezone.now()
                consultation.status = 'in_progress'
                consultation.save()
                
            elif event_type == 'meeting.ended':
                consultation.actual_end = timezone.now()
                consultation.status = 'completed'
                if consultation.actual_start:
                    duration = consultation.actual_end - consultation.actual_start
                    consultation.duration_minutes = int(duration.total_seconds() / 60)
                consultation.save()
                
            elif event_type == 'recording.completed':
                recording_files = payload.get('payload', {}).get('object', {}).get('recording_files', [])
                if recording_files:
                    consultation.recording_url = recording_files[0].get('download_url', '')
                    consultation.save()
            
            return {'status': 'processed', 'event': event_type}
            
        except Consultation.DoesNotExist:
            logger.warning(f"Consultation not found for meeting ID: {meeting_id}")
            return {'error': 'Consultation not found'}


class EnhancedGoogleMeetService(BaseVideoProvider):
    """Enhanced Google Meet integration using Calendar API"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = 'google_meet'
        self.service_account_file = settings.TELEMEDICINE_CONFIG.get('GOOGLE_SERVICE_ACCOUNT_FILE')
        self.scopes = ['https://www.googleapis.com/auth/calendar']
    
    def _get_calendar_service(self):
        """Get authenticated Google Calendar service"""
        if not self.service_account_file:
            raise VideoProviderError("Google service account file not configured")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes)
            service = build('calendar', 'v3', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            raise VideoProviderError(f"Google authentication failed: {e}")
    
    def create_meeting(self, consultation) -> Dict[str, Any]:
        """Create Google Meet via Calendar API"""
        service = self._get_calendar_service()
        
        # Create calendar event with Google Meet
        event = {
            'summary': f"Medical Consultation: Dr. {consultation.doctor.get_full_name()} with {consultation.patient.get_full_name()}",
            'description': f"Virtual medical consultation for {consultation.patient.get_full_name()}",
            'start': {
                'dateTime': consultation.scheduled_start.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (consultation.scheduled_start + timedelta(hours=1)).isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [
                {'email': consultation.doctor.email, 'responseStatus': 'accepted'},
                {'email': consultation.patient.email, 'responseStatus': 'needsAction'},
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"consultation-{consultation.id}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 15},       # 15 minutes before
                ],
            },
        }
        
        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            meet_link = created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
            meeting_id = created_event.get('conferenceData', {}).get('conferenceId', '')
            
            consultation.meeting_id = meeting_id or created_event['id']
            consultation.meeting_url = meet_link
            consultation.save()
            
            return {
                'meeting_id': meeting_id or created_event['id'],
                'meeting_url': meet_link,
                'calendar_event_id': created_event['id'],
                'provider': self.provider_name,
                'calendar_link': created_event.get('htmlLink', ''),
            }
            
        except HttpError as e:
            logger.error(f"Failed to create Google Meet: {e}")
            raise VideoProviderError(f"Google Meet creation failed: {e}")


class VideoProviderFactory:
    """Enhanced factory for video provider services"""
    
    _services = {
        'jitsi': EnhancedJitsiService,
        'zoom': EnhancedZoomService,
        'google_meet': EnhancedGoogleMeetService,
    }
    
    @classmethod
    def get_service(cls, provider: str) -> BaseVideoProvider:
        """Get the appropriate video provider service"""
        if provider not in cls._services:
            raise ValueError(f"Unsupported video provider: {provider}")
        
        service_class = cls._services[provider]
        return service_class()
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict[str, Any]]:
        """Get list of available and configured providers"""
        providers = {}
        
        for provider_name, service_class in cls._services.items():
            try:
                service = service_class()
                providers[provider_name] = {
                    'name': provider_name,
                    'display_name': provider_name.replace('_', ' ').title(),
                    'available': True,
                    'features': cls._get_provider_features(provider_name)
                }
            except Exception as e:
                providers[provider_name] = {
                    'name': provider_name,
                    'display_name': provider_name.replace('_', ' ').title(),
                    'available': False,
                    'error': str(e)
                }
        
        return providers
    
    @classmethod
    def _get_provider_features(cls, provider: str) -> Dict[str, bool]:
        """Get features supported by each provider"""
        features = {
            'jitsi': {
                'recording': True,
                'screen_sharing': True,
                'chat': True,
                'waiting_room': False,
                'authentication': True,
                'webhooks': False,
                'participant_management': True,
            },
            'zoom': {
                'recording': True,
                'screen_sharing': True,
                'chat': True,
                'waiting_room': True,
                'authentication': True,
                'webhooks': True,
                'participant_management': True,
                'breakout_rooms': True,
            },
            'google_meet': {
                'recording': True,
                'screen_sharing': True,
                'chat': True,
                'waiting_room': True,
                'authentication': True,
                'webhooks': False,
                'participant_management': False,
                'calendar_integration': True,
            }
        }
        
        return features.get(provider, {})


class EnhancedConsultationService:
    """Enhanced service for managing consultations"""
    
    def __init__(self):
        self.video_factory = VideoProviderFactory()
    
    def create_consultation_with_meeting(
        self, 
        booking=None, 
        doctor=None, 
        patient=None,
        video_provider='jitsi', 
        **kwargs
    ) -> Tuple[Any, Dict[str, Any]]:
        """Create consultation and associated video meeting"""
        from .models import Consultation
        
        if booking:
            doctor = booking.doctor
            patient = booking.patient
            scheduled_start = timezone.datetime.combine(
                booking.appointment_date,
                booking.appointment_time,
                timezone.get_current_timezone()
            )
        else:
            if not doctor or not patient:
                raise ValueError("Doctor and patient are required when no booking is provided")
            scheduled_start = kwargs.get('scheduled_start', timezone.now() + timedelta(minutes=30))
        
        # Create consultation
        consultation = Consultation.objects.create(
            booking=booking,
            doctor=doctor,
            patient=patient,
            video_provider=video_provider,
            scheduled_start=scheduled_start,
            **kwargs
        )
        
        # Create video meeting
        try:
            video_service = self.video_factory.get_service(video_provider)
            meeting_info = video_service.create_meeting(consultation)
            
            # Send notifications
            self._send_consultation_notifications(consultation, meeting_info)
            
            return consultation, meeting_info
        except Exception as e:
            # Rollback consultation creation if meeting creation fails
            consultation.delete()
            raise VideoProviderError(f"Failed to create video meeting: {e}")
    
    def _send_consultation_notifications(self, consultation, meeting_info):
        """Send notifications to participants"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        # Email notifications
        try:
            # Doctor notification
            doctor_context = {
                'consultation': consultation,
                'meeting_info': meeting_info,
                'recipient_name': consultation.doctor.get_full_name(),
                'role': 'doctor'
            }
            
            doctor_subject = f"Virtual Consultation Scheduled - {consultation.patient.get_full_name()}"
            doctor_message = render_to_string('emails/consultation_created_doctor.html', doctor_context)
            
            send_mail(
                subject=doctor_subject,
                message='',
                html_message=doctor_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[consultation.doctor.email],
                fail_silently=True
            )
            
            # Patient notification
            patient_context = {
                'consultation': consultation,
                'meeting_info': meeting_info,
                'recipient_name': consultation.patient.get_full_name(),
                'role': 'patient'
            }
            
            patient_subject = f"Virtual Consultation Scheduled with Dr. {consultation.doctor.get_full_name()}"
            patient_message = render_to_string('emails/consultation_created_patient.html', patient_context)
            
            send_mail(
                subject=patient_subject,
                message='',
                html_message=patient_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[consultation.patient.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send consultation notifications: {e}")
    
    def handle_provider_webhook(self, provider: str, payload: Dict[str, Any], signature: str = '') -> Dict[str, Any]:
        """Handle webhook from video provider"""
        try:
            video_service = self.video_factory.get_service(provider)
            
            if not video_service.validate_webhook(payload, signature):
                raise ValueError("Invalid webhook signature")
            
            return video_service.handle_webhook(payload)
        except Exception as e:
            logger.error(f"Failed to handle {provider} webhook: {e}")
            return {'error': str(e)}