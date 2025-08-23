from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Q
from django.utils import timezone

from mixins.custom_mixins import DoctorRequiredMixin
from bookings.models import Booking


class DoctorTelemedicineView(DoctorRequiredMixin, LoginRequiredMixin, TemplateView):
    """
    Doctor's telemedicine dashboard view
    """
    template_name = 'doctors/telemedicine.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user
        
        try:
            # Import here to avoid circular imports
            from telemedicine.models import Consultation
            
            # Get doctor's consultations
            consultations = Consultation.objects.filter(
                doctor=doctor
            ).select_related('patient', 'booking').order_by('-scheduled_at')
            
            # Separate by status
            upcoming_consultations = consultations.filter(status='scheduled')
            completed_consultations = consultations.filter(status='completed')
            
            context.update({
                'consultations': consultations[:10],
                'upcoming_consultations': upcoming_consultations[:5],
                'completed_consultations': completed_consultations[:5],
                'total_consultations': consultations.count(),
                'upcoming_count': upcoming_consultations.count(),
                'completed_count': completed_consultations.count(),
            })
        except ImportError:
            # If telemedicine app is not available, show placeholder data
            context.update({
                'consultations': [],
                'upcoming_consultations': [],
                'completed_consultations': [],
                'total_consultations': 0,
                'upcoming_count': 0,
                'completed_count': 0,
                'telemedicine_not_available': True,
            })
        
        return context


class DoctorSOAPNotesView(DoctorRequiredMixin, LoginRequiredMixin, TemplateView):
    """
    Doctor's SOAP notes management view
    """
    template_name = 'doctors/soap-notes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user
        
        try:
            # Import here to avoid circular imports
            from core.models import SoapNote
            
            # Get doctor's SOAP notes
            soap_notes = SoapNote.objects.filter(
                created_by=doctor
            ).select_related('patient').order_by('-created_at')
            
            # Get recent patients for quick access
            recent_patients = Booking.objects.filter(
                doctor=doctor,
                status='completed'
            ).select_related('patient').order_by('-appointment_date')[:10]
            
            context.update({
                'soap_notes': soap_notes[:20],
                'recent_patients': recent_patients,
                'total_notes': soap_notes.count(),
            })
        except ImportError:
            # If SOAP notes model is not available, show placeholder data
            context.update({
                'soap_notes': [],
                'recent_patients': [],
                'total_notes': 0,
                'soap_not_available': True,
            })
        
        return context