from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import SoapNote, EHRRecord, AuditLog, Speciality, Review
from .serializers import (
    SoapNoteSerializer, SoapNoteListSerializer,
    EHRRecordSerializer, EHRRecordListSerializer,
    AuditLogSerializer, PatientSearchSerializer,
    SpecialitySerializer, ReviewSerializer
)
from mixins.custom_mixins import DoctorRequiredMixin, PatientRequiredMixin
from accounts.models import User
from bookings.models import Booking
from vitals.models import VitalRecord, VitalCategory


# CSRF Token endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token for React frontend"""
    token = get_token(request)
    return Response({'csrfToken': token})

# Health check endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now(),
        'version': '1.0.0'
    })

# Custom authentication views
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    """Custom token authentication with user data"""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_staff': user.is_staff,
                }
            })
        else:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User registration endpoint"""
    try:
        data = request.data
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
        # Check required fields
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user already exists
        if User.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'patient')
        )
        
        # Create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_staff': user.is_staff,
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """User logout endpoint"""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'})
    except Exception as e:
        return Response({'message': 'Logged out'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current user details"""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    user = request.user
    
    if user.role == 'doctor':
        # Doctor dashboard stats
        today = timezone.now().date()
        try:
            upcoming_appointments = Booking.objects.filter(
                doctor=user,
                date__gte=today,
                status='confirmed'
            ).count()
            
            total_patients = Booking.objects.filter(
                doctor=user,
                status='completed'
            ).values('patient').distinct().count()
            
            avg_rating = Review.objects.filter(doctor=user).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating'] or 0
            
            return Response({
                'upcoming_appointments': upcoming_appointments,
                'total_patients': total_patients,
                'average_rating': round(avg_rating, 1),
                'total_reviews': Review.objects.filter(doctor=user).count(),
            })
        except Exception as e:
            return Response({
                'upcoming_appointments': 0,
                'total_patients': 0,
                'average_rating': 0,
                'total_reviews': 0,
                'error': str(e)
            })
        
    elif user.role == 'patient':
        # Patient dashboard stats
        today = timezone.now().date()
        try:
            upcoming_appointments = Booking.objects.filter(
                patient=user,
                date__gte=today,
                status='confirmed'
            ).count()
            
            total_appointments = Booking.objects.filter(
                patient=user,
                status='completed'
            ).count()
            
            recent_vitals = VitalRecord.objects.filter(
                patient=user
            ).order_by('-recorded_at')[:5]
            
            last_appointment = Booking.objects.filter(
                patient=user,
                status='completed'
            ).order_by('-date').first()
            
            return Response({
                'upcoming_appointments': upcoming_appointments,
                'total_appointments': total_appointments,
                'recent_vitals_count': recent_vitals.count(),
                'last_appointment': last_appointment.date if last_appointment else None,
            })
        except Exception as e:
            return Response({
                'upcoming_appointments': 0,
                'total_appointments': 0,
                'recent_vitals_count': 0,
                'last_appointment': None,
                'error': str(e)
            })
    
    return Response({'message': 'Dashboard data not available for this role'})


class SpecialityViewSet(viewsets.ReadOnlyModelViewSet):
    """Speciality API viewset"""
    queryset = Speciality.objects.filter(is_active=True)
    serializer_class = SpecialitySerializer
    permission_classes = [AllowAny]

class ReviewViewSet(viewsets.ModelViewSet):
    """Review API viewset"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'doctor':
            return Review.objects.filter(doctor=self.request.user)
        elif self.request.user.role == 'patient':
            return Review.objects.filter(patient=self.request.user)
        return Review.objects.none()

class SoapNoteViewSet(viewsets.ModelViewSet):
    """SOAP Notes API viewset"""
    serializer_class = SoapNoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'doctor':
            return SoapNote.objects.filter(created_by=self.request.user)
        elif self.request.user.role == 'patient':
            return SoapNote.objects.filter(patient=self.request.user)
        return SoapNote.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EHRRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EHR Records
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__username']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'doctor':
            # Doctors can see EHR records of their patients
            return EHRRecord.objects.filter(
                patient__patient_appointments__doctor=user
            ).distinct().select_related('patient', 'patient__profile', 'last_updated_by')
        elif user.role == 'patient':
            # Patients can see their own EHR record
            return EHRRecord.objects.filter(patient=user).select_related(
                'patient', 'patient__profile', 'last_updated_by'
            )
        elif user.is_superuser:
            # Admins can see all EHR records
            return EHRRecord.objects.all().select_related(
                'patient', 'patient__profile', 'last_updated_by'
            )
        else:
            return EHRRecord.objects.none()

    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return EHRRecordListSerializer
        return EHRRecordSerializer

    def perform_create(self, serializer):
        """Create EHR record and log the action"""
        ehr_record = serializer.save()
        
        # Log the action
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='EHRRecord',
            object_id=ehr_record.id,
            object_repr=str(ehr_record),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        """Update EHR record and log the action"""
        ehr_record = serializer.save()
        
        # Log the action
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='EHRRecord',
            object_id=ehr_record.id,
            object_repr=str(ehr_record),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_destroy(self, instance):
        """Delete EHR record and log the action"""
        # Log the action before deletion
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            model_name='EHRRecord',
            object_id=instance.id,
            object_repr=str(instance),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        instance.delete()

    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=True, methods=['post'])
    def add_vital_signs(self, request, pk=None):
        """Add vital signs to EHR record"""
        ehr_record = self.get_object()
        vital_signs_data = request.data
        
        try:
            ehr_record.add_vital_signs(vital_signs_data)
            return Response({"message": "Vital signs added successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def add_lab_result(self, request, pk=None):
        """Add lab result to EHR record"""
        ehr_record = self.get_object()
        test_name = request.data.get('test_name')
        result_data = request.data.get('result_data', {})
        
        if not test_name:
            return Response(
                {"error": "test_name is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ehr_record.add_lab_result(test_name, result_data)
            return Response({"message": "Lab result added successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def add_imaging_result(self, request, pk=None):
        """Add imaging result to EHR record"""
        ehr_record = self.get_object()
        study_type = request.data.get('study_type')
        result_data = request.data.get('result_data', {})
        
        if not study_type:
            return Response(
                {"error": "study_type is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ehr_record.add_imaging_result(study_type, result_data)
            return Response({"message": "Imaging result added successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def my_record(self, request):
        """Get current user's EHR record (patients only)"""
        if request.user.role != 'patient':
            return Response(
                {"error": "Only patients can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            ehr_record = EHRRecord.objects.get(patient=request.user)
            serializer = EHRRecordSerializer(ehr_record)
            return Response(serializer.data)
        except EHRRecord.DoesNotExist:
            return Response(
                {"error": "EHR record not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Audit Logs (read-only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'model_name']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            # Admins can see all audit logs
            return AuditLog.objects.all().select_related('user')
        elif user.role == 'doctor':
            # Doctors can see audit logs related to their actions
            return AuditLog.objects.filter(user=user).select_related('user')
        else:
            # Patients can only see their own audit logs
            return AuditLog.objects.filter(user=user).select_related('user')


class PatientSearchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for patient search (doctors only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSearchSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'last_name', 'date_joined']
    ordering = ['first_name', 'last_name']

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'doctor':
            # Doctors can search for their patients
            return User.objects.filter(
                role='patient',
                patient_appointments__doctor=user
            ).distinct().select_related('profile')
        elif user.is_superuser:
            # Admins can search for all patients
            return User.objects.filter(role='patient').select_related('profile')
        else:
            return User.objects.none()

    @action(detail=False, methods=['get'])
    def by_condition(self, request):
        """Search patients by medical condition"""
        if request.user.role not in ['doctor', 'admin']:
            return Response(
                {"error": "Unauthorized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        condition = request.query_params.get('condition')
        if not condition:
            return Response(
                {"error": "condition parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search in SOAP notes and EHR records
        patients = User.objects.filter(
            Q(role='patient') &
            (Q(soap_notes__subjective__icontains=condition) |
             Q(soap_notes__objective__icontains=condition) |
             Q(soap_notes__assessment__icontains=condition) |
             Q(ehr_record__medical_history__icontains=condition) |
             Q(profile__medical_conditions__icontains=condition))
        ).distinct().select_related('profile')
        
        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)
