from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction

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
from bookings.models import Booking
from mixins.custom_mixins import DoctorRequiredMixin, PatientRequiredMixin


class ConsultationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing consultations
    """
    permission_classes = [IsAuthenticated]
    
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
        elif user.role == 'admin':
            return Consultation.objects.all().select_related(
                'booking', 'doctor', 'patient'
            ).prefetch_related('participants', 'messages')
        else:
            return Consultation.objects.none()
    
    def perform_create(self, serializer):
        """Create consultation with proper validation"""
        booking_id = serializer.validated_data['booking_id']
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Ensure user has permission to create consultation for this booking
        user = self.request.user
        if user.role == 'doctor' and booking.doctor != user:
            raise PermissionError("You can only create consultations for your own appointments")
        elif user.role == 'patient' and booking.patient != user:
            raise PermissionError("You can only create consultations for your own appointments")
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a consultation"""
        consultation = self.get_object()
        serializer = ConsultationActionSerializer(
            data={'action': 'start'},
            context={'consultation': consultation, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        
        if consultation.start_consultation():
            return Response({
                'message': 'Consultation started successfully',
                'status': consultation.status,
                'actual_start': consultation.actual_start
            })
        else:
            return Response(
                {'error': 'Could not start consultation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a consultation"""
        consultation = self.get_object()
        serializer = ConsultationActionSerializer(
            data={'action': 'end', 'notes': request.data.get('notes', '')},
            context={'consultation': consultation, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        
        if consultation.end_consultation():
            if serializer.validated_data.get('notes'):
                consultation.notes = serializer.validated_data['notes']
                consultation.save()
            
            return Response({
                'message': 'Consultation ended successfully',
                'status': consultation.status,
                'actual_end': consultation.actual_end,
                'duration_minutes': consultation.duration_minutes
            })
        else:
            return Response(
                {'error': 'Could not end consultation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a consultation"""
        consultation = self.get_object()
        serializer = ConsultationActionSerializer(
            data={'action': 'cancel', 'notes': request.data.get('notes', '')},
            context={'consultation': consultation, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            consultation.status = ConsultationStatus.CANCELLED
            if serializer.validated_data.get('notes'):
                consultation.notes = serializer.validated_data['notes']
            consultation.save()
            
            # Update booking status
            consultation.booking.status = 'cancelled'
            consultation.booking.save()
        
        return Response({
            'message': 'Consultation cancelled successfully',
            'status': consultation.status
        })
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get consultation messages"""
        consultation = self.get_object()
        messages = consultation.messages.all()
        
        # Filter private messages for non-medical staff
        if request.user.role not in ['doctor', 'admin']:
            messages = messages.filter(is_private=False)
        
        serializer = ConsultationMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in consultation"""
        consultation = self.get_object()
        
        # Ensure user is a participant
        if request.user.id not in [consultation.doctor.id, consultation.patient.id]:
            return Response(
                {'error': 'Only consultation participants can send messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ConsultationMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(
            consultation=consultation,
            sender=request.user
        )
        
        return Response(ConsultationMessageSerializer(message).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get consultation participants"""
        consultation = self.get_object()
        participants = consultation.participants.all()
        serializer = ConsultationParticipantSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def waiting_room(self, request, pk=None):
        """Get waiting room status"""
        consultation = self.get_object()
        try:
            waiting_room = consultation.waiting_room
            serializer = WaitingRoomSerializer(waiting_room)
            return Response(serializer.data)
        except WaitingRoom.DoesNotExist:
            return Response({'message': 'No waiting room found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def join_waiting_room(self, request, pk=None):
        """Join waiting room (for patients)"""
        consultation = self.get_object()
        
        if request.user.role != 'patient' or consultation.patient != request.user:
            return Response(
                {'error': 'Only the assigned patient can join the waiting room'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        waiting_room, created = WaitingRoom.objects.get_or_create(
            consultation=consultation,
            defaults={'patient_joined_at': timezone.now()}
        )
        
        if not created and not waiting_room.patient_joined_at:
            waiting_room.patient_joined_at = timezone.now()
            waiting_room.save()
        
        serializer = WaitingRoomSerializer(waiting_room)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def recording(self, request, pk=None):
        """Get consultation recording"""
        consultation = self.get_object()
        try:
            recording = consultation.recording
            serializer = ConsultationRecordingSerializer(recording)
            return Response(serializer.data)
        except ConsultationRecording.DoesNotExist:
            return Response({'message': 'No recording found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def technical_issues(self, request, pk=None):
        """Get technical issues for consultation"""
        consultation = self.get_object()
        issues = consultation.technical_issues.all()
        serializer = TechnicalIssueSerializer(issues, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def report_issue(self, request, pk=None):
        """Report a technical issue"""
        consultation = self.get_object()
        
        # Ensure user is a participant
        if request.user.id not in [consultation.doctor.id, consultation.patient.id]:
            return Response(
                {'error': 'Only consultation participants can report issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TechnicalIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        issue = serializer.save(
            consultation=consultation,
            reporter=request.user
        )
        
        return Response(TechnicalIssueSerializer(issue).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming consultations for the user"""
        queryset = self.get_queryset().filter(
            scheduled_start__gte=timezone.now(),
            status__in=[ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING]
        ).order_by('scheduled_start')
        
        serializer = ConsultationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active consultations for the user"""
        queryset = self.get_queryset().filter(
            status__in=[ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]
        ).order_by('scheduled_start')
        
        serializer = ConsultationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get consultation statistics"""
        queryset = self.get_queryset()
        
        total_consultations = queryset.count()
        completed_consultations = queryset.filter(status=ConsultationStatus.COMPLETED).count()
        upcoming_consultations = queryset.filter(
            scheduled_start__gte=timezone.now(),
            status__in=[ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING]
        ).count()
        active_consultations = queryset.filter(
            status__in=[ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]
        ).count()
        
        # Calculate average duration
        completed_queryset = queryset.filter(
            status=ConsultationStatus.COMPLETED,
            duration_minutes__isnull=False
        )
        avg_duration = completed_queryset.aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
        total_duration = completed_queryset.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
        
        # Group by provider
        by_provider = dict(queryset.values('video_provider').annotate(count=Count('id')).values_list('video_provider', 'count'))
        
        # Group by status
        by_status = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        
        stats = {
            'total_consultations': total_consultations,
            'completed_consultations': completed_consultations,
            'upcoming_consultations': upcoming_consultations,
            'active_consultations': active_consultations,
            'average_duration': round(avg_duration, 2),
            'total_duration': total_duration,
            'by_provider': by_provider,
            'by_status': by_status,
        }
        
        serializer = ConsultationStatsSerializer(stats)
        return Response(serializer.data)


class VideoProviderViewSet(viewsets.ViewSet):
    """
    ViewSet for video provider information
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get available video providers"""
        providers = [
            {'value': choice[0], 'label': choice[1]}
            for choice in VideoProvider.choices
        ]
        serializer = VideoProviderChoicesSerializer(providers, many=True)
        return Response(serializer.data)


class TechnicalIssueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing technical issues
    """
    serializer_class = TechnicalIssueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter issues based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            return TechnicalIssue.objects.all().select_related(
                'consultation', 'reporter'
            )
        else:
            # Users can only see issues from their own consultations
            return TechnicalIssue.objects.filter(
                Q(consultation__doctor=user) | Q(consultation__patient=user)
            ).select_related('consultation', 'reporter')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved (admin only)"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only administrators can resolve issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        issue = self.get_object()
        issue.resolved = True
        issue.resolved_at = timezone.now()
        issue.resolution_notes = request.data.get('resolution_notes', '')
        issue.save()
        
        serializer = TechnicalIssueSerializer(issue)
        return Response(serializer.data)


# Booking integration views
class BookingConsultationViewSet(viewsets.ViewSet):
    """
    ViewSet for creating consultations from bookings
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='create-consultation')
    def create_consultation(self, request, pk=None):
        """Create a consultation for a booking"""
        booking = get_object_or_404(Booking, id=pk)
        
        # Check permissions
        user = request.user
        if user.role == 'doctor' and booking.doctor != user:
            return Response(
                {'error': 'You can only create consultations for your own appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'patient' and booking.patient != user:
            return Response(
                {'error': 'You can only create consultations for your own appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if consultation already exists
        if hasattr(booking, 'consultation'):
            return Response(
                {'error': 'Consultation already exists for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create consultation
        data = request.data.copy()
        data['booking_id'] = booking.id
        
        serializer = ConsultationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        consultation = serializer.save()
        
        return Response(
            ConsultationSerializer(consultation).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'], url_path='consultation')
    def get_consultation(self, request, pk=None):
        """Get consultation for a booking"""
        booking = get_object_or_404(Booking, id=pk)
        
        # Check permissions
        user = request.user
        if user.role == 'doctor' and booking.doctor != user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'patient' and booking.patient != user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            consultation = booking.consultation
            serializer = ConsultationSerializer(consultation)
            return Response(serializer.data)
        except Consultation.DoesNotExist:
            return Response(
                {'message': 'No consultation found for this booking'},
                status=status.HTTP_404_NOT_FOUND
            )