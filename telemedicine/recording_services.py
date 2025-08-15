import os
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.cache import cache
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class RecordingError(Exception):
    """Custom exception for recording operations"""
    pass


class BaseRecordingService:
    """Base class for recording services"""
    
    def __init__(self, provider: str):
        self.provider = provider
        self.storage_backend = default_storage
        
    def start_recording(self, consultation) -> Dict[str, Any]:
        """Start recording for consultation"""
        raise NotImplementedError
    
    def stop_recording(self, consultation) -> Dict[str, Any]:
        """Stop recording for consultation"""
        raise NotImplementedError
    
    def get_recording_status(self, consultation) -> Dict[str, Any]:
        """Get recording status"""
        raise NotImplementedError
    
    def process_recording(self, recording_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process completed recording"""
        raise NotImplementedError
    
    def get_download_url(self, recording_id: str, user, expires_in: int = 3600) -> str:
        """Generate secure download URL"""
        raise NotImplementedError
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete recording"""
        raise NotImplementedError


class ZoomRecordingService(BaseRecordingService):
    """Zoom recording service with cloud storage integration"""
    
    def __init__(self):
        super().__init__('zoom')
        from .enhanced_services import EnhancedZoomService
        self.zoom_service = EnhancedZoomService()
    
    def start_recording(self, consultation) -> Dict[str, Any]:
        """Start Zoom cloud recording"""
        try:
            # Zoom recordings are controlled via meeting settings
            # This would typically be set when creating the meeting
            if consultation.recording_enabled:
                return {
                    'status': 'started',
                    'recording_type': 'cloud',
                    'provider': self.provider,
                    'message': 'Cloud recording will start automatically when meeting begins'
                }
            else:
                raise RecordingError("Recording not enabled for this consultation")
                
        except Exception as e:
            logger.error(f"Failed to start Zoom recording: {e}")
            raise RecordingError(f"Failed to start recording: {e}")
    
    def stop_recording(self, consultation) -> Dict[str, Any]:
        """Stop Zoom cloud recording"""
        try:
            # Zoom recordings stop automatically when meeting ends
            return {
                'status': 'stopped',
                'provider': self.provider,
                'message': 'Recording will be processed and available shortly'
            }
        except Exception as e:
            logger.error(f"Failed to stop Zoom recording: {e}")
            raise RecordingError(f"Failed to stop recording: {e}")
    
    def get_recording_status(self, consultation) -> Dict[str, Any]:
        """Get Zoom recording status"""
        try:
            recording_info = self.zoom_service.get_recording_info(consultation.meeting_id)
            if recording_info:
                return {
                    'status': 'available',
                    'recordings': recording_info.get('recording_files', []),
                    'total_size': sum(f.get('file_size', 0) for f in recording_info.get('recording_files', [])),
                    'duration': recording_info.get('duration'),
                    'provider': self.provider
                }
            else:
                return {
                    'status': 'not_available',
                    'provider': self.provider
                }
        except Exception as e:
            logger.error(f"Failed to get Zoom recording status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def process_recording(self, recording_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Zoom recording webhook data"""
        try:
            from .models import ConsultationRecordingSegment
            
            recording_files = recording_data.get('recording_files', [])
            processed_segments = []
            
            for file_data in recording_files:
                # Create recording segment
                segment = ConsultationRecordingSegment.objects.create(
                    consultation_id=recording_data.get('consultation_id'),
                    segment_id=file_data.get('id'),
                    file_url=file_data.get('download_url'),
                    file_size_bytes=file_data.get('file_size'),
                    duration_seconds=file_data.get('duration'),
                    start_time=datetime.fromisoformat(file_data.get('recording_start')),
                    end_time=datetime.fromisoformat(file_data.get('recording_end')),
                    video_quality=file_data.get('resolution', ''),
                    processing_status='completed'
                )
                
                processed_segments.append({
                    'id': str(segment.id),
                    'file_type': file_data.get('file_type'),
                    'file_size': file_data.get('file_size'),
                    'duration': file_data.get('duration')
                })
            
            return {
                'status': 'processed',
                'segments': processed_segments,
                'provider': self.provider
            }
            
        except Exception as e:
            logger.error(f"Failed to process Zoom recording: {e}")
            raise RecordingError(f"Failed to process recording: {e}")


class JitsiRecordingService(BaseRecordingService):
    """Jitsi recording service with local storage"""
    
    def __init__(self):
        super().__init__('jitsi')
        self.recording_directory = getattr(settings, 'JITSI_RECORDING_DIR', '/tmp/recordings')
    
    def start_recording(self, consultation) -> Dict[str, Any]:
        """Start Jitsi recording (requires Jibri setup)"""
        try:
            if not consultation.recording_enabled:
                raise RecordingError("Recording not enabled for this consultation")
            
            # This would integrate with Jibri (Jitsi Broadcasting Infrastructure)
            recording_id = f"consultation_{consultation.id}_{int(timezone.now().timestamp())}"
            
            # In a real implementation, this would call Jitsi API to start recording
            recording_data = {
                'recording_id': recording_id,
                'status': 'started',
                'start_time': timezone.now().isoformat(),
                'provider': self.provider
            }
            
            # Cache recording session data
            cache.set(f"jitsi_recording_{consultation.id}", recording_data, timeout=7200)
            
            return recording_data
            
        except Exception as e:
            logger.error(f"Failed to start Jitsi recording: {e}")
            raise RecordingError(f"Failed to start recording: {e}")
    
    def stop_recording(self, consultation) -> Dict[str, Any]:
        """Stop Jitsi recording"""
        try:
            recording_data = cache.get(f"jitsi_recording_{consultation.id}")
            if not recording_data:
                raise RecordingError("No active recording found")
            
            recording_data['status'] = 'stopped'
            recording_data['end_time'] = timezone.now().isoformat()
            
            # Update cache
            cache.set(f"jitsi_recording_{consultation.id}", recording_data, timeout=7200)
            
            return recording_data
            
        except Exception as e:
            logger.error(f"Failed to stop Jitsi recording: {e}")
            raise RecordingError(f"Failed to stop recording: {e}")


class GoogleMeetRecordingService(BaseRecordingService):
    """Google Meet recording service"""
    
    def __init__(self):
        super().__init__('google_meet')
    
    def start_recording(self, consultation) -> Dict[str, Any]:
        """Start Google Meet recording"""
        try:
            if not consultation.recording_enabled:
                raise RecordingError("Recording not enabled for this consultation")
            
            # Google Meet recordings are controlled by the meeting host
            return {
                'status': 'started',
                'provider': self.provider,
                'message': 'Recording must be started manually by the meeting host'
            }
            
        except Exception as e:
            logger.error(f"Failed to start Google Meet recording: {e}")
            raise RecordingError(f"Failed to start recording: {e}")
    
    def get_recording_status(self, consultation) -> Dict[str, Any]:
        """Get Google Meet recording status"""
        # Google Meet recordings are stored in Google Drive
        # This would require Drive API integration
        return {
            'status': 'check_drive',
            'provider': self.provider,
            'message': 'Check Google Drive for recording availability'
        }


class RecordingManager:
    """Central recording management service"""
    
    def __init__(self):
        self.services = {
            'zoom': ZoomRecordingService(),
            'jitsi': JitsiRecordingService(),
            'google_meet': GoogleMeetRecordingService(),
        }
    
    def get_service(self, provider: str) -> BaseRecordingService:
        """Get recording service for provider"""
        service = self.services.get(provider)
        if not service:
            raise RecordingError(f"Unsupported recording provider: {provider}")
        return service
    
    def start_consultation_recording(self, consultation) -> Dict[str, Any]:
        """Start recording for consultation"""
        try:
            service = self.get_service(consultation.video_provider)
            result = service.start_recording(consultation)
            
            # Update consultation recording status
            consultation.recording_enabled = True
            consultation.save()
            
            # Log recording start
            self._log_recording_event(consultation, 'started', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to start recording for consultation {consultation.id}: {e}")
            raise
    
    def stop_consultation_recording(self, consultation) -> Dict[str, Any]:
        """Stop recording for consultation"""
        try:
            service = self.get_service(consultation.video_provider)
            result = service.stop_recording(consultation)
            
            # Log recording stop
            self._log_recording_event(consultation, 'stopped', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop recording for consultation {consultation.id}: {e}")
            raise
    
    def get_consultation_recordings(self, consultation) -> Dict[str, Any]:
        """Get all recordings for consultation"""
        try:
            service = self.get_service(consultation.video_provider)
            recordings = service.get_recording_status(consultation)
            
            # Add access information
            recordings['access_info'] = self._get_access_permissions(consultation)
            
            return recordings
            
        except Exception as e:
            logger.error(f"Failed to get recordings for consultation {consultation.id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_secure_access_url(self, consultation, user, recording_id: str, expires_in: int = 3600) -> str:
        """Generate secure access URL for recording"""
        try:
            # Verify user has access to this consultation
            if not self._verify_recording_access(consultation, user):
                raise RecordingError("User does not have access to this recording")
            
            service = self.get_service(consultation.video_provider)
            return service.get_download_url(recording_id, user, expires_in)
            
        except Exception as e:
            logger.error(f"Failed to generate access URL: {e}")
            raise
    
    def process_recording_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process recording webhook from provider"""
        try:
            service = self.get_service(provider)
            result = service.process_recording(payload)
            
            # Update consultation with recording URL
            if 'consultation_id' in payload:
                self._update_consultation_recording(payload['consultation_id'], result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process recording webhook from {provider}: {e}")
            raise
    
    def delete_consultation_recording(self, consultation, recording_id: str, user) -> bool:
        """Delete recording (admin only)"""
        try:
            # Verify user has delete permissions
            if user.role != 'admin' and user != consultation.doctor:
                raise RecordingError("Insufficient permissions to delete recording")
            
            service = self.get_service(consultation.video_provider)
            success = service.delete_recording(recording_id)
            
            if success:
                # Log deletion
                self._log_recording_event(consultation, 'deleted', {
                    'recording_id': recording_id,
                    'deleted_by': user.id
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete recording {recording_id}: {e}")
            raise
    
    def get_recording_analytics(self, consultation) -> Dict[str, Any]:
        """Get recording analytics and metrics"""
        try:
            from .models import ConsultationRecordingSegment
            
            segments = ConsultationRecordingSegment.objects.filter(
                consultation=consultation
            )
            
            total_duration = sum(s.duration_seconds or 0 for s in segments)
            total_size = sum(s.file_size_bytes or 0 for s in segments)
            
            return {
                'total_segments': segments.count(),
                'total_duration_seconds': total_duration,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'average_quality': self._calculate_average_quality(segments),
                'download_count': sum(s.download_count for s in segments),
                'last_accessed': max(s.created_at for s in segments) if segments else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get recording analytics: {e}")
            return {}
    
    def _verify_recording_access(self, consultation, user) -> bool:
        """Verify user has access to recording"""
        return (
            user == consultation.doctor or
            user == consultation.patient or
            user.role == 'admin' or
            user.has_perm('telemedicine.can_access_recordings')
        )
    
    def _get_access_permissions(self, consultation) -> Dict[str, Any]:
        """Get access permissions for recording"""
        return {
            'doctor_access': True,
            'patient_access': True,
            'admin_access': True,
            'expiry_days': getattr(settings, 'RECORDING_RETENTION_DAYS', 90),
            'download_enabled': True,
            'streaming_enabled': True,
        }
    
    def _log_recording_event(self, consultation, event_type: str, data: Dict[str, Any]):
        """Log recording events for audit trail"""
        try:
            log_entry = {
                'consultation_id': str(consultation.id),
                'event_type': event_type,
                'timestamp': timezone.now().isoformat(),
                'provider': consultation.video_provider,
                'data': data
            }
            
            # Store in cache for recent events
            cache_key = f"recording_events_{consultation.id}"
            events = cache.get(cache_key, [])
            events.append(log_entry)
            cache.set(cache_key, events[-50:], timeout=86400)  # Keep last 50 events for 24h
            
            logger.info(f"Recording event logged: {event_type} for consultation {consultation.id}")
            
        except Exception as e:
            logger.error(f"Failed to log recording event: {e}")
    
    def _update_consultation_recording(self, consultation_id: str, recording_data: Dict[str, Any]):
        """Update consultation with recording information"""
        try:
            from .models import Consultation
            
            consultation = Consultation.objects.get(id=consultation_id)
            
            # Update recording URL if available
            if 'download_url' in recording_data:
                consultation.recording_url = recording_data['download_url']
                consultation.save()
            
        except Exception as e:
            logger.error(f"Failed to update consultation recording: {e}")
    
    def _calculate_average_quality(self, segments) -> str:
        """Calculate average recording quality"""
        if not segments:
            return 'unknown'
        
        quality_scores = {'high': 3, 'medium': 2, 'low': 1}
        total_score = 0
        count = 0
        
        for segment in segments:
            if segment.video_quality in quality_scores:
                total_score += quality_scores[segment.video_quality]
                count += 1
        
        if count == 0:
            return 'unknown'
        
        avg_score = total_score / count
        if avg_score >= 2.5:
            return 'high'
        elif avg_score >= 1.5:
            return 'medium'
        else:
            return 'low'


class RecordingSecurityService:
    """Service for recording security and access control"""
    
    @staticmethod
    def generate_access_token(user_id: int, recording_id: str, expires_in: int = 3600) -> str:
        """Generate secure access token for recording"""
        payload = {
            'user_id': user_id,
            'recording_id': recording_id,
            'expires_at': int((timezone.now() + timedelta(seconds=expires_in)).timestamp())
        }
        
        # Create signed token
        import jwt
        secret_key = settings.SECRET_KEY
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify and decode access token"""
        try:
            import jwt
            
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Check expiration
            if timezone.now().timestamp() > payload['expires_at']:
                raise RecordingError("Access token has expired")
            
            return payload
            
        except jwt.InvalidTokenError as e:
            raise RecordingError(f"Invalid access token: {e}")
    
    @staticmethod
    def create_secure_url(base_url: str, token: str) -> str:
        """Create secure URL with embedded token"""
        from urllib.parse import urlencode
        
        params = {'token': token}
        return f"{base_url}?{urlencode(params)}"
    
    @staticmethod
    def log_access_attempt(user_id: int, recording_id: str, success: bool, ip_address: str = None):
        """Log recording access attempts"""
        try:
            log_entry = {
                'user_id': user_id,
                'recording_id': recording_id,
                'success': success,
                'timestamp': timezone.now().isoformat(),
                'ip_address': ip_address
            }
            
            # Store in cache for security monitoring
            cache_key = f"recording_access_log_{recording_id}"
            logs = cache.get(cache_key, [])
            logs.append(log_entry)
            cache.set(cache_key, logs[-100:], timeout=86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Failed to log access attempt: {e}")


# Global recording manager instance
recording_manager = RecordingManager()