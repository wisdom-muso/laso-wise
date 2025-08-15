from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import json
import logging

from .models import (
    Consultation, ConsultationMessage, ConsultationParticipant,
    ConsultationRecording, WaitingRoom, TechnicalIssue,
    VideoProvider, ConsultationStatus
)
from .serializers import (
    ConsultationSerializer, ConsultationCreateSerializer, ConsultationListSerializer,
    ConsultationMessageSerializer, ConsultationParticipantSerializer,
    ConsultationRecordingSerializer, WaitingRoomSerializer,
    TechnicalIssueSerializer, ConsultationActionSerializer,
    VideoProviderChoicesSerializer, ConsultationStatsSerializer
)
from .enhanced_services import (
    VideoProviderFactory, EnhancedConsultationService, VideoProviderError
)
from bookings.models import Booking
from mixins.custom_mixins import DoctorRequiredMixin, PatientRequiredMixin

logger = logging.getLogger(__name__)


class EnhancedConsultationViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for managing consultations with video integration"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consultation_service = EnhancedConsultationService()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConsultationCreateSerializer
        elif self.action == 'list':
            return ConsultationListSerializer
        return ConsultationSerializer
    
    def get_queryset(self):
        """Filter consultations based on user role"""
        user = self.request.user
        
        if user.role == 'doctor':
            return Consultation.objects.filter(doctor=user).select_related(
                'booking', 'doctor', 'patient'
            ).prefetch_related('participants', 'messages')
        elif user.role == 'patient':
            return Consultation.objects.filter(patient=user).select_related(
                'booking', 'doctor', 'patient'
            ).prefetch_related('participants', 'messages')
        else:
            return Consultation.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create consultation with video meeting"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Get booking if provided
                booking_id = serializer.validated_data.pop('booking_id', None)
                booking = None
                if booking_id:
                    booking = get_object_or_404(Booking, id=booking_id)
                    if booking.consultation:
                        return Response(
                            {'error': 'Consultation already exists for this booking'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Get doctor and patient
                doctor_id = serializer.validated_data.pop('doctor_id', None)
                patient_id = serializer.validated_data.pop('patient_id', None)
                
                if booking:
                    doctor = booking.doctor
                    patient = booking.patient
                else:
                    if not doctor_id or not patient_id:
                        return Response(
                            {'error': 'Doctor and patient IDs required when no booking provided'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    doctor = get_object_or_404(request.user.__class__, id=doctor_id, role='doctor')
                    patient = get_object_or_404(request.user.__class__, id=patient_id, role='patient')
                
                # Create consultation with meeting
                consultation, meeting_info = self.consultation_service.create_consultation_with_meeting(
                    booking=booking,
                    doctor=doctor,
                    patient=patient,
                    **serializer.validated_data
                )
                
                # Serialize response
                response_serializer = ConsultationSerializer(consultation)
                response_data = response_serializer.data
                response_data['meeting_info'] = meeting_info
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except VideoProviderError as e:
            return Response(
                {'error': f'Failed to create video meeting: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to create consultation: {e}")
            return Response(
                {'error': 'Failed to create consultation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a consultation"""
        consultation = self.get_object()
        
        # Check permissions
        if request.user != consultation.doctor and request.user != consultation.patient:
            return Response(
                {'error': 'Only consultation participants can start the consultation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if consultation.start_consultation():
            # Send WebSocket notification
            self._send_websocket_notification(consultation, 'consultation_started', {
                'started_by': request.user.get_full_name(),
                'timestamp': consultation.actual_start.isoformat() if consultation.actual_start else None,
            })
            
            return Response({'status': 'started'})
        else:
            return Response(
                {'error': 'Cannot start consultation at this time'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a consultation"""
        consultation = self.get_object()
        
        # Only doctor can end consultation
        if request.user != consultation.doctor:
            return Response(
                {'error': 'Only the doctor can end the consultation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notes = request.data.get('notes', '')
        
        if consultation.end_consultation():
            if notes:
                consultation.notes = notes
                consultation.save()
            
            # Send WebSocket notification
            self._send_websocket_notification(consultation, 'consultation_ended', {
                'ended_by': request.user.get_full_name(),
                'timestamp': consultation.actual_end.isoformat() if consultation.actual_end else None,
                'duration_minutes': consultation.duration_minutes,
                'notes': notes,
            })
            
            return Response({
                'status': 'ended',
                'duration_minutes': consultation.duration_minutes
            })
        else:
            return Response(
                {'error': 'Cannot end consultation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def join_waiting(self, request, pk=None):
        """Join the waiting room"""
        consultation = self.get_object()
        
        # Check permissions
        if request.user != consultation.doctor and request.user != consultation.patient:
            return Response(
                {'error': 'Only consultation participants can join waiting room'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        waiting_room, created = WaitingRoom.objects.get_or_create(
            consultation=consultation,
            defaults={'queue_position': 1}
        )
        
        if request.user == consultation.patient:
            waiting_room.patient_joined_at = timezone.now()
        
        if request.user == consultation.doctor:
            waiting_room.doctor_notified_at = timezone.now()
        
        waiting_room.save()
        
        consultation.status = ConsultationStatus.WAITING
        consultation.save()
        
        # Send WebSocket notification
        self._send_websocket_notification(consultation, 'user_joined_waiting', {
            'user_name': request.user.get_full_name(),
            'user_role': request.user.role,
            'timestamp': timezone.now().isoformat(),
        })
        
        return Response({
            'status': 'joined_waiting_room',
            'queue_position': waiting_room.queue_position,
            'estimated_wait_minutes': waiting_room.estimated_wait_minutes
        })
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in the consultation"""
        consultation = self.get_object()
        
        # Check permissions
        if request.user != consultation.doctor and request.user != consultation.patient:
            return Response(
                {'error': 'Only consultation participants can send messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ConsultationMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = ConsultationMessage.objects.create(
            consultation=consultation,
            sender=request.user,
            **serializer.validated_data
        )
        
        # Send WebSocket notification
        self._send_websocket_notification(consultation, 'new_message', {
            'message_id': message.id,
            'sender_name': request.user.get_full_name(),
            'sender_role': request.user.role,
            'message': message.message,
            'message_type': message.message_type,
            'timestamp': message.timestamp.isoformat(),
            'is_private': message.is_private,
        })
        
        response_serializer = ConsultationMessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def report_issue(self, request, pk=None):
        """Report a technical issue"""
        consultation = self.get_object()
        
        # Check permissions
        if request.user != consultation.doctor and request.user != consultation.patient:
            return Response(
                {'error': 'Only consultation participants can report issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TechnicalIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        issue = TechnicalIssue.objects.create(
            consultation=consultation,
            reporter=request.user,
            **serializer.validated_data
        )
        
        # Send WebSocket notification
        self._send_websocket_notification(consultation, 'technical_issue_reported', {
            'issue_id': issue.id,
            'reporter_name': request.user.get_full_name(),
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'description': issue.description,
            'timestamp': issue.created_at.isoformat(),
        })
        
        response_serializer = TechnicalIssueSerializer(issue)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_connection_quality(self, request, pk=None):
        """Update connection quality"""
        consultation = self.get_object()
        quality = request.data.get('quality')
        
        if quality not in ['excellent', 'good', 'fair', 'poor']:
            return Response(
                {'error': 'Invalid quality value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.connection_quality = quality
        consultation.save()
        
        # Send WebSocket notification
        self._send_websocket_notification(consultation, 'connection_quality_updated', {
            'user_name': request.user.get_full_name(),
            'quality': quality,
            'timestamp': timezone.now().isoformat(),
        })
        
        return Response({'status': 'updated', 'quality': quality})
    
    @action(detail=True, methods=['get'])
    def meeting_info(self, request, pk=None):
        """Get meeting information from video provider"""
        consultation = self.get_object()
        
        try:
            video_service = VideoProviderFactory.get_service(consultation.video_provider)
            meeting_info = video_service.get_meeting_info(consultation.meeting_id)
            return Response(meeting_info)
        except Exception as e:
            logger.error(f"Failed to get meeting info: {e}")
            return Response(
                {'error': 'Failed to get meeting information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def recording(self, request, pk=None):
        """Get recording information"""
        consultation = self.get_object()
        
        try:
            video_service = VideoProviderFactory.get_service(consultation.video_provider)
            recording_info = video_service.get_recording_info(consultation.meeting_id)
            
            if recording_info:
                return Response(recording_info)
            else:
                return Response(
                    {'message': 'No recording available'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Failed to get recording info: {e}")
            return Response(
                {'error': 'Failed to get recording information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get consultation statistics"""
        user = request.user
        
        # Get basic stats
        if user.role == 'doctor':
            queryset = Consultation.objects.filter(doctor=user)
        elif user.role == 'patient':
            queryset = Consultation.objects.filter(patient=user)
        else:
            return Response({'error': 'Invalid user role'}, status=status.HTTP_403_FORBIDDEN)
        
        total = queryset.count()
        completed = queryset.filter(status=ConsultationStatus.COMPLETED).count()
        upcoming = queryset.filter(
            scheduled_start__gte=timezone.now(),
            status__in=[ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING]
        ).count()
        active = queryset.filter(
            status__in=[ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]
        ).count()
        
        # Calculate averages
        avg_duration = queryset.filter(
            status=ConsultationStatus.COMPLETED,
            duration_minutes__isnull=False
        ).aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
        
        total_duration = queryset.filter(
            duration_minutes__isnull=False
        ).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
        
        # Provider breakdown
        by_provider = {}
        for provider in VideoProvider.choices:
            count = queryset.filter(video_provider=provider[0]).count()
            by_provider[provider[1]] = count
        
        # Status breakdown
        by_status = {}
        for status_choice in ConsultationStatus.choices:
            count = queryset.filter(status=status_choice[0]).count()
            by_status[status_choice[1]] = count
        
        stats = {
            'total_consultations': total,
            'completed_consultations': completed,
            'upcoming_consultations': upcoming,
            'active_consultations': active,
            'average_duration': round(avg_duration, 2),
            'total_duration': total_duration,
            'by_provider': by_provider,
            'by_status': by_status,
        }
        
        return Response(stats)
    
    def _send_websocket_notification(self, consultation, event_type, data):
        """Send WebSocket notification to consultation participants"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'consultation_{consultation.id}',
                {
                    'type': event_type,
                    'consultation_id': str(consultation.id),
                    **data
                }
            )


class VideoProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for video provider information"""
    permission_classes = [IsAuthenticated]
    serializer_class = VideoProviderChoicesSerializer
    
    def list(self, request, *args, **kwargs):
        """Get available video providers with their features"""
        providers = VideoProviderFactory.get_available_providers()
        return Response(providers)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(APIView):
    """Handle webhooks from video providers"""
    permission_classes = [AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consultation_service = EnhancedConsultationService()
    
    def post(self, request, provider):
        """Handle webhook from specific provider"""
        if provider not in ['zoom', 'google_meet', 'jitsi']:
            return Response(
                {'error': 'Unsupported provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get signature from headers
            signature = request.META.get('HTTP_X_SIGNATURE', '')
            if not signature and provider == 'zoom':
                signature = request.META.get('HTTP_AUTHORIZATION', '')
            
            # Parse payload
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON payload'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Handle webhook
            result = self.consultation_service.handle_provider_webhook(
                provider=provider,
                payload=payload,
                signature=signature
            )
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Webhook handling failed for {provider}: {e}")
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConsultationRecordingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for consultation recordings"""
    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationRecordingSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'doctor':
            return ConsultationRecording.objects.filter(
                consultation__doctor=user,
                is_available=True
            ).select_related('consultation')
        elif user.role == 'patient':
            return ConsultationRecording.objects.filter(
                consultation__patient=user,
                is_available=True
            ).select_related('consultation')
        else:
            return ConsultationRecording.objects.none()


class TechnicalIssueViewSet(viewsets.ModelViewSet):
    """ViewSet for technical issues"""
    permission_classes = [IsAuthenticated]
    serializer_class = TechnicalIssueSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'doctor':
            return TechnicalIssue.objects.filter(
                consultation__doctor=user
            ).select_related('consultation', 'reporter')
        elif user.role == 'patient':
            return TechnicalIssue.objects.filter(
                consultation__patient=user
            ).select_related('consultation', 'reporter')
        else:
            return TechnicalIssue.objects.none()
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved"""
        issue = self.get_object()
        
        # Only doctor or admin can resolve issues
        if request.user.role not in ['doctor', 'admin']:
            return Response(
                {'error': 'Only doctors can resolve issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        issue.resolved = True
        issue.resolved_at = timezone.now()
        issue.resolution_notes = resolution_notes
        issue.save()
        
        return Response({
            'status': 'resolved',
            'resolved_at': issue.resolved_at.isoformat(),
            'resolution_notes': resolution_notes
        })


class BookingConsultationViewSet(viewsets.ModelViewSet):
    """ViewSet for linking bookings with consultations"""
    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationCreateSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consultation_service = EnhancedConsultationService()
    
    def get_queryset(self):
        """Get bookings that can have consultations"""
        user = self.request.user
        
        if user.role == 'doctor':
            return Booking.objects.filter(
                doctor=user,
                status__in=['confirmed', 'scheduled'],
                consultation__isnull=True  # No consultation created yet
            )
        elif user.role == 'patient':
            return Booking.objects.filter(
                patient=user,
                status__in=['confirmed', 'scheduled'],
                consultation__isnull=True
            )
        else:
            return Booking.objects.none()
    
    @action(detail=True, methods=['post'])
    def create_consultation(self, request, pk=None):
        """Create consultation for a specific booking"""
        booking = get_object_or_404(Booking, pk=pk)
        
        # Check permissions
        if request.user != booking.doctor and request.user != booking.patient:
            return Response(
                {'error': 'Only booking participants can create consultations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if consultation already exists
        if hasattr(booking, 'consultation') and booking.consultation:
            return Response(
                {'error': 'Consultation already exists for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get video provider preference
        video_provider = request.data.get('video_provider', 'jitsi')
        recording_enabled = request.data.get('recording_enabled', False)
        notes = request.data.get('notes', '')
        
        try:
            consultation, meeting_info = self.consultation_service.create_consultation_with_meeting(
                booking=booking,
                video_provider=video_provider,
                recording_enabled=recording_enabled,
                notes=notes
            )
            
            # Serialize response
            serializer = ConsultationSerializer(consultation)
            response_data = serializer.data
            response_data['meeting_info'] = meeting_info
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except VideoProviderError as e:
            return Response(
                {'error': f'Failed to create video meeting: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to create consultation for booking {booking.id}: {e}")
            return Response(
                {'error': 'Failed to create consultation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )