from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.http import Http404

from .models import SoapNote, EHRRecord, AuditLog
from .serializers import (
    SoapNoteSerializer, SoapNoteListSerializer,
    EHRRecordSerializer, EHRRecordListSerializer,
    AuditLogSerializer, PatientSearchSerializer
)
from mixins.custom_mixins import DoctorRequiredMixin, PatientRequiredMixin
from accounts.models import User


class SoapNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SOAP Notes
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'appointment', 'created_by', 'is_draft']
    search_fields = ['subjective', 'objective', 'assessment', 'plan']
    ordering_fields = ['created_at', 'updated_at', 'appointment__appointment_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'doctor':
            # Doctors can see SOAP notes they created
            return SoapNote.objects.filter(created_by=user).select_related(
                'patient', 'patient__profile', 'appointment', 'created_by'
            )
        elif user.role == 'patient':
            # Patients can see SOAP notes related to their appointments
            return SoapNote.objects.filter(patient=user).select_related(
                'patient', 'patient__profile', 'appointment', 'created_by'
            )
        elif user.is_superuser:
            # Admins can see all SOAP notes
            return SoapNote.objects.all().select_related(
                'patient', 'patient__profile', 'appointment', 'created_by'
            )
        else:
            return SoapNote.objects.none()

    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return SoapNoteListSerializer
        return SoapNoteSerializer

    def perform_create(self, serializer):
        """Create SOAP note and log the action"""
        soap_note = serializer.save()
        
        # Log the action
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='SoapNote',
            object_id=soap_note.id,
            object_repr=str(soap_note),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        """Update SOAP note and log the action"""
        soap_note = serializer.save()
        
        # Log the action
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='SoapNote',
            object_id=soap_note.id,
            object_repr=str(soap_note),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_destroy(self, instance):
        """Delete SOAP note and log the action"""
        # Log the action before deletion
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            model_name='SoapNote',
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

    @action(detail=False, methods=['get'])
    def my_notes(self, request):
        """Get SOAP notes for the current user (doctor)"""
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        notes = self.get_queryset().filter(created_by=request.user)
        serializer = SoapNoteListSerializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def patient_notes(self, request):
        """Get SOAP notes for a specific patient (doctors only)"""
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {"error": "patient_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = self.get_queryset().filter(patient_id=patient_id)
        serializer = SoapNoteListSerializer(notes, many=True)
        return Response(serializer.data)


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
