"""
Telemedicine Views for Laso Healthcare
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
import json
import uuid
import time
from datetime import datetime

from .models import TeleMedicineConsultation, TeleMedicineMessage, TeleMedicineSettings, TelemedicineAppointment, VideoSession, TelemedDocument, TelemedPrescription, TelemedNote
from appointments.models import Appointment
from core.models_notifications import Notification, NotificationType
from .forms import TelemedicineAppointmentForm, TelemedDocumentForm, TelemedPrescriptionForm, TelemedNoteForm, AppointmentSearchForm


class TeleMedicineConsultationListView(LoginRequiredMixin, ListView):
    """
    Telemedicine consultation list
    """
    model = TeleMedicineConsultation
    template_name = 'telemedicine/session_list.html'
    context_object_name = 'consultations'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_doctor():
            return TeleMedicineConsultation.objects.filter(
                appointment__doctor=user
            ).order_by('-scheduled_start_time')
        elif user.is_patient():
            return TeleMedicineConsultation.objects.filter(
                appointment__patient=user
            ).order_by('-scheduled_start_time')
        else:
            return TeleMedicineConsultation.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Today's consultations
        today_consultations = self.get_queryset().filter(
            scheduled_start_time__date=timezone.now().date()
        )
        
        context['today_consultations'] = today_consultations
        context['upcoming_count'] = self.get_queryset().filter(
            status='scheduled',
            scheduled_start_time__gt=timezone.now()
        ).count()
        
        # Add search form
        context['search_form'] = AppointmentSearchForm(self.request.GET)
        
        return context


class TeleMedicineConsultationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Telemedicine consultation detail
    """
    model = TeleMedicineConsultation
    template_name = 'telemedicine/consultation_detail.html'
    context_object_name = 'consultation'
    
    def test_func(self):
        consultation = self.get_object()
        user = self.request.user
        
        # Only doctor and patient can access
        return user in [consultation.appointment.doctor, consultation.appointment.patient]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consultation = self.get_object()
        
        # Chat messages
        context['chat_messages'] = consultation.chat_messages.all()
        
        # Can the user join?
        context['can_join'] = consultation.can_join(self.request.user)
        context['join_url'] = consultation.get_join_url()
        
        # Consultation status
        context['is_active'] = consultation.is_active()
        context['time_until_start'] = None
        
        if consultation.scheduled_start_time > timezone.now():
            context['time_until_start'] = consultation.scheduled_start_time - timezone.now()
        
        return context


@login_required
@require_http_methods(["POST"])
def create_telemedicine_consultation(request, appointment_id):
    """
    Create telemedicine consultation for appointment
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Only doctor can create
    if not request.user.is_doctor() or appointment.doctor != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Does a consultation already exist?
    if hasattr(appointment, 'telemedicine_consultation'):
        return JsonResponse({'error': 'Consultation already exists'}, status=400)
    
    try:
        data = json.loads(request.body)
        consultation_type = data.get('consultation_type', 'video')
        
        # Create consultation
        consultation = TeleMedicineConsultation.objects.create(
            appointment=appointment,
            consultation_type=consultation_type,
            scheduled_start_time=timezone.make_aware(
                datetime.combine(appointment.date, appointment.time)
            ),
            platform='internal'
        )
        
        # Send notification to patient
        Notification.objects.create(
            recipient=appointment.patient,
            sender=request.user,
            notification_type=NotificationType.APPOINTMENT_CONFIRMED,
            title=_('Telemedicine Appointment Created'),
            message=_(f'Online consultation prepared for your appointment with Dr. {request.user.get_full_name()} on {appointment.date}.'),
            related_object=consultation
        )
        
        return JsonResponse({
            'success': True,
            'consultation_id': consultation.id,
            'meeting_id': str(consultation.meeting_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class TeleMedicineConsultationJoinView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Join a telemedicine consultation
    """
    def test_func(self):
        session_id = self.kwargs.get('session_id')
        consultation = get_object_or_404(TeleMedicineConsultation, meeting_id=session_id)
        return consultation.can_join(self.request.user)

    def get(self, request, *args, **kwargs):
        session_id = self.kwargs.get('session_id')
        consultation = get_object_or_404(TeleMedicineConsultation, meeting_id=session_id)
        consultation.mark_as_started(request.user)
        return render(request, 'telemedicine/consultation_room.html', {
            'consultation': consultation,
            'user_role': 'doctor' if request.user.is_doctor() else 'patient',
            'is_doctor': request.user.is_doctor(),
            'is_patient': request.user.is_patient()
        })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_consultation_message(request, consultation_id):
    """
    Send a message during a consultation
    """
    consultation = get_object_or_404(TeleMedicineConsultation, id=consultation_id)
    
    # Access control
    if not consultation.can_join(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        message_type = data.get('type', 'text')
        
        if not content:
            return JsonResponse({'error': 'Message content required'}, status=400)
        
        # Create message
        message = TeleMedicineMessage.objects.create(
            consultation=consultation,
            sender=request.user,
            message_type=message_type,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'sender': message.sender.get_full_name(),
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'type': message.message_type
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_consultation_messages(request, consultation_id):
    """
    Get consultation messages
    """
    consultation = get_object_or_404(TeleMedicineConsultation, id=consultation_id)
    
    # Access control
    if not consultation.can_join(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    messages = consultation.chat_messages.all().order_by('timestamp')
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'sender': message.sender.get_full_name(),
            'sender_id': message.sender.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'type': message.message_type,
            'is_own': message.sender == request.user
        })
    
    return JsonResponse({
        'messages': messages_data
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def end_consultation(request, consultation_id):
    """
    End a consultation
    """
    consultation = get_object_or_404(TeleMedicineConsultation, id=consultation_id)
    
    # Only doctor can end
    if not request.user.is_doctor() or consultation.appointment.doctor != request.user:
        return JsonResponse({'error': 'Only doctor can end consultation'}, status=403)
    
    try:
        data = json.loads(request.body)
        consultation_notes = data.get('notes', '')
        patient_feedback = data.get('patient_feedback', '')
        
        # End consultation
        consultation.mark_as_completed()
        consultation.consultation_notes = consultation_notes
        consultation.patient_feedback = patient_feedback
        consultation.save()
        
        # Complete the appointment
        appointment = consultation.appointment
        appointment.status = 'completed'
        appointment.save()
        
        # Send notification to patient and doctor
        Notification.objects.create(
            recipient=appointment.patient,
            sender=request.user,
            notification_type=NotificationType.TREATMENT_COMPLETED,
            title=_('Telemedicine Consultation Completed'),
            message=_(f'Your online consultation with Dr. {request.user.get_full_name()} has been completed.'),
            related_object=consultation
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Consultation ended successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required 
@require_http_methods(["POST"])
def update_consultation_status(request, consultation_id):
    """
    Update consultation status
    """
    consultation = get_object_or_404(TeleMedicineConsultation, id=consultation_id)
    
    # Access control
    if not consultation.can_join(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        status = data.get('status')
        connection_quality = data.get('connection_quality')
        technical_issues = data.get('technical_issues', '')
        
        if status and status in dict(TeleMedicineConsultation.STATUS_CHOICES):
            consultation.status = status
        
        if connection_quality:
            consultation.connection_quality = connection_quality
        
        if technical_issues:
            consultation.technical_issues = technical_issues
        
        consultation.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class TeleMedicineConsultationCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new telemedicine consultation
    """
    model = TeleMedicineConsultation
    template_name = 'telemedicine/schedule_consultation.html'
    fields = ['appointment', 'consultation_type', 'platform', 'notes']
    success_url = reverse_lazy('telemedicine:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        # Filter appointments based on user type
        if user.is_doctor():
            form.fields['appointment'].queryset = Appointment.objects.filter(
                doctor=user,
                status='planned'
            )
        elif user.is_patient():
            form.fields['appointment'].queryset = Appointment.objects.filter(
                patient=user,
                status='planned'
            )
        
        return form
    
    def form_valid(self, form):
        consultation = form.save(commit=False)
        appointment = consultation.appointment
        
        # Set scheduled start time from appointment
        consultation.scheduled_start_time = timezone.make_aware(
            datetime.combine(appointment.date, appointment.time)
        )
        
        # Generate meeting ID
        consultation.meeting_id = str(uuid.uuid4())
        consultation.status = 'scheduled'
        
        consultation.save()
        
        messages.success(self.request, 'Telemedicine consultation scheduled successfully.')
        return super().form_valid(form)


class TeleMedicineSettingsView(LoginRequiredMixin, UpdateView):
    """
    Telemedicine settings
    """
    model = TeleMedicineSettings
    template_name = 'telemedicine/settings.html'
    fields = [
        'default_camera_enabled', 'default_microphone_enabled', 'video_quality',
        'consultation_reminders', 'reminder_minutes_before', 'email_notifications',
        'sms_notifications', 'require_waiting_room', 'allow_recording',
        'allow_file_sharing', 'max_consultation_duration', 'auto_end_consultation'
    ]
    success_url = reverse_lazy('telemedicine-settings')
    
    def get_object(self, queryset=None):
        settings, created = TeleMedicineSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def form_valid(self, form):
        messages.success(self.request, _('Telemedicine settings updated successfully.'))
        return super().form_valid(form)


@login_required
@require_http_methods(["GET"])
def consultation_analytics(request):
    """
    Telemedicine analytics
    """
    if not request.user.is_doctor():
        return JsonResponse({'error': 'Only doctors can access analytics'}, status=403)
    
    # Last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=30)
    
    consultations = TeleMedicineConsultation.objects.filter(
        appointment__doctor=request.user,
        scheduled_start_time__date__range=[start_date, end_date]
    )
    
    analytics = {
        'total_consultations': consultations.count(),
        'completed_consultations': consultations.filter(status='completed').count(),
        'cancelled_consultations': consultations.filter(status='cancelled').count(),
        'average_duration': 0,
        'total_duration': 0,
        'patient_satisfaction': 0,
        'connection_quality_stats': {},
        'daily_stats': []
    }
    
    # Calculate average duration
    completed = consultations.filter(status='completed', duration_minutes__isnull=False)
    if completed.exists():
        total_duration = sum(c.duration_minutes for c in completed)
        analytics['total_duration'] = total_duration
        analytics['average_duration'] = total_duration / completed.count()
    
    # Patient satisfaction
    rated_consultations = consultations.filter(patient_rating__isnull=False)
    if rated_consultations.exists():
        total_rating = sum(c.patient_rating for c in rated_consultations)
        analytics['patient_satisfaction'] = total_rating / rated_consultations.count()
    
    # Connection quality statistics
    quality_stats = consultations.values('connection_quality').annotate(
        count=models.Count('connection_quality')
    )
    analytics['connection_quality_stats'] = {
        item['connection_quality']: item['count'] for item in quality_stats
    }
    
    return JsonResponse(analytics)


@login_required
def telemedicine_dashboard(request):
    """
    Telemedicine dashboard
    """
    user = request.user
    
    if user.is_doctor():
        # Doctor dashboard
        upcoming_consultations = TeleMedicineConsultation.objects.filter(
            appointment__doctor=user,
            status='scheduled',
            scheduled_start_time__gt=timezone.now()
        ).order_by('scheduled_start_time')[:5]
        
        today_consultations = TeleMedicineConsultation.objects.filter(
            appointment__doctor=user,
            scheduled_start_time__date=timezone.now().date()
        )
        
        context = {
            'upcoming_consultations': upcoming_consultations,
            'today_consultations': today_consultations,
            'today_count': today_consultations.count(),
            'user_type': 'doctor'
        }
        
    elif user.is_patient():
        # Patient dashboard
        next_consultation = TeleMedicineConsultation.objects.filter(
            appointment__patient=user,
            status='scheduled',
            scheduled_start_time__gt=timezone.now()
        ).order_by('scheduled_start_time').first()
        
        recent_consultations = TeleMedicineConsultation.objects.filter(
            appointment__patient=user,
            status='completed'
        ).order_by('-scheduled_start_time')[:5]
        
        context = {
            'next_consultation': next_consultation,
            'recent_consultations': recent_consultations,
            'user_type': 'patient'
        }
    
    else:
        context = {'user_type': 'other'}
    
    return render(request, 'telemedicine/dashboard.html', context)


@login_required
def create_telemedicine_appointment(request):
    if request.method == 'POST':
        form = TelemedicineAppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            
            # Assignment based on user type
            if request.user.is_patient():
                appointment.patient = request.user
            else:
                appointment.created_by = request.user
                
            appointment.save()
            
            # Create notification for doctor
            Notification.objects.create(
                recipient=appointment.doctor,
                notification_type=NotificationType.APPOINTMENT_CONFIRMED,
                title="New Telemedicine Appointment",
                message=f"You have a new telemedicine appointment with {appointment.patient.get_full_name()} on {appointment.date.strftime('%d.%m.%Y')} at {appointment.time.strftime('%H:%M')}.",
                priority="normal",
                extra_data={
                    "appointment_id": appointment.id,
                    "patient_id": appointment.patient.id,
                }
            )
            
            # Create notification for patient (if not created by patient)
            if not request.user.is_patient():
                Notification.objects.create(
                    recipient=appointment.patient,
                    notification_type=NotificationType.APPOINTMENT_CONFIRMED,
                    title="New Telemedicine Appointment",
                    message=f"A new telemedicine appointment has been created with Dr. {appointment.doctor.get_full_name()} on {appointment.date.strftime('%d.%m.%Y')} at {appointment.time.strftime('%H:%M')}.",
                    priority="normal",
                    extra_data={
                        "appointment_id": appointment.id,
                        "doctor_id": appointment.doctor.id,
                    }
                )
            
            messages.success(request, "Telemedicine appointment created successfully.")
            return redirect('telemedicine:appointment-detail', pk=appointment.pk)
    else:
        form = TelemedicineAppointmentForm(user=request.user)
        
    return render(request, 'telemedicine/appointment_form.html', {'form': form})


@login_required
def start_video_session(request, appointment_id):
    appointment = get_object_or_404(TelemedicineAppointment, id=appointment_id)
    
    # Authorization check
    if not (request.user == appointment.doctor or request.user == appointment.patient):
        messages.error(request, "You do not have permission to access this session.")
        return redirect('telemedicine:appointment-list')
    
    # Appointment time check
    now = timezone.now()
    appointment_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.time))
    time_diff = (appointment_datetime - now).total_seconds() / 60  # In minutes
    
    # Allow access 10 minutes before or 30 minutes after appointment
    if time_diff > 10:
        messages.warning(request, f"The session has not started yet. Your appointment is at {appointment.time.strftime('%H:%M')}.")
        return redirect('telemedicine:appointment-detail', pk=appointment_id)
    
    if time_diff < -30:
        messages.warning(request, "This appointment has expired. Please create a new appointment.")
        return redirect('telemedicine:appointment-list')
    
    # Check if there is an active session
    active_session = VideoSession.objects.filter(
        appointment=appointment,
        end_time__isnull=True
    ).first()
    
    # If not, start a new session
    if not active_session:
        active_session = VideoSession.objects.create(
            appointment=appointment,
            started_by=request.user,
            room_name=f"telemed_{appointment.id}_{int(time.time())}"
        )
        
        # Send notification to the other party
        recipient = appointment.patient if request.user == appointment.doctor else appointment.doctor
        Notification.objects.create(
            recipient=recipient,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            title="Session Started",
            message=f"{request.user.get_full_name()} has started the session. You can join now.",
            priority="high",
            extra_data={
                "appointment_id": appointment.id,
                "session_id": active_session.id,
            }
        )
    
    # Redirect to the session page
    return render(request, 'telemedicine/video_session.html', {
        'appointment': appointment,
        'session': active_session,
        'is_doctor': request.user == appointment.doctor
    })


@login_required
def end_video_session(request, session_id):
    session = get_object_or_404(VideoSession, id=session_id)
    appointment = session.appointment
    
    # Authorization check
    if not (request.user == appointment.doctor or request.user == appointment.patient):
        messages.error(request, "You do not have permission for this operation.")
        return JsonResponse({'status': 'error', 'message': 'Permission error'})
    
    # End the session
    if not session.end_time:
        session.end_time = timezone.now()
        session.ended_by = request.user
        session.save()
    
    return JsonResponse({'status': 'success'})


class TelemedicineAppointmentListView(LoginRequiredMixin, ListView):
    model = TelemedicineAppointment
    template_name = 'telemedicine/appointment_list.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        user = self.request.user
        queryset = TelemedicineAppointment.objects.all()
        
        # Filter by user type
        if user.is_patient():
            queryset = queryset.filter(patient=user)
        elif user.is_doctor():
            queryset = queryset.filter(doctor=user)
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Date filter
        date_filter = self.request.GET.get('date_filter', 'upcoming')
        today = timezone.now().date()
        
        if date_filter == 'upcoming':
            queryset = queryset.filter(date__gte=today)
        elif date_filter == 'past':
            queryset = queryset.filter(date__lt=today)
        
        return queryset.order_by('date', 'time')


class TelemedicineAppointmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = TelemedicineAppointment
    template_name = 'telemedicine/appointment_detail.html'
    context_object_name = 'appointment'
    
    def test_func(self):
        appointment = self.get_object()
        user = self.request.user
        return (user == appointment.doctor or 
                user == appointment.patient or 
                user.is_receptionist() or 
                user.is_admin_user())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.get_object()
        
        # Add documents
        context['documents'] = TelemedDocument.objects.filter(appointment=appointment)
        
        # Add prescriptions
        context['prescriptions'] = TelemedPrescription.objects.filter(appointment=appointment)
        
        # Add notes
        context['notes'] = TelemedNote.objects.filter(appointment=appointment)
        
        # Add session history
        context['sessions'] = VideoSession.objects.filter(appointment=appointment)
        
        # Is there an active session?
        context['active_session'] = VideoSession.objects.filter(
            appointment=appointment,
            end_time__isnull=True
        ).first()
        
        # Add forms
        if self.request.user == appointment.doctor:
            context['document_form'] = TelemedDocumentForm()
            context['prescription_form'] = TelemedPrescriptionForm()
            context['note_form'] = TelemedNoteForm()
        
        return context


@login_required
def upload_telemed_document(request, appointment_id):
    appointment = get_object_or_404(TelemedicineAppointment, id=appointment_id)
    
    if request.method == 'POST':
        form = TelemedDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.appointment = appointment
            document.uploaded_by = request.user
            document.save()
            
            messages.success(request, "Document uploaded successfully.")
        else:
            messages.error(request, "Error uploading document.")
    
    return redirect('telemedicine:appointment-detail', pk=appointment_id)


@login_required
def create_telemed_prescription(request, appointment_id):
    appointment = get_object_or_404(TelemedicineAppointment, id=appointment_id)
    
    if request.method == 'POST':
        form = TelemedPrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.appointment = appointment
            prescription.created_by = request.user
            prescription.save()
            
            messages.success(request, "Prescription created successfully.")
        else:
            messages.error(request, "Error creating prescription.")
    
    return redirect('telemedicine:appointment-detail', pk=appointment_id)


@login_required
def create_telemed_note(request, appointment_id):
    appointment = get_object_or_404(TelemedicineAppointment, id=appointment_id)
    
    if request.method == 'POST':
        form = TelemedNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.appointment = appointment
            note.created_by = request.user
            note.save()
            
            messages.success(request, "Note created successfully.")
        else:
            messages.error(request, "Error creating note.")
    
    return redirect('telemedicine:appointment-detail', pk=appointment_id)


class TeleconsultationAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'telemedicine/analytics.html'
    
    def test_func(self):
        return self.request.user.is_doctor() or self.request.user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        consultations = TeleMedicineConsultation.objects.filter(
            scheduled_start_time__date__range=[start_date, end_date]
        )
        
        # Doctor filter
        if self.request.user.is_doctor():
            consultations = consultations.filter(appointment__doctor=self.request.user)
        
        context['total_consultations'] = consultations.count()
        context['completed_consultations'] = consultations.filter(status='completed').count()
        context['cancelled_consultations'] = consultations.filter(status='cancelled').count()
        
        # Average duration
        completed = consultations.filter(status='completed', duration_minutes__isnull=False)
        if completed.exists():
            total_duration = sum(c.duration_minutes for c in completed)
            context['average_duration'] = total_duration / completed.count()
        else:
            context['average_duration'] = 0
        
        # Daily statistics
        daily_stats = consultations.values('scheduled_start_time__date').annotate(
            count=models.Count('id')
        ).order_by('scheduled_start_time__date')
        
        context['daily_stats_labels'] = [
            item['scheduled_start_time__date'].strftime('%d.%m') for item in daily_stats
        ]
        context['daily_stats_data'] = [item['count'] for item in daily_stats]
        
        return context


@csrf_exempt
@require_http_methods(["POST"])
def webrtc_signal(request, session_id):
    """
    WebRTC signaling server (simple)
    """
    try:
        data = json.loads(request.body)
        # This part should be integrated with a real WebRTC signaling server
        # For example, a WebSocket server or Redis pub/sub can be used
        print(f"Received signal for session {session_id}: {data}")
        return JsonResponse({'status': 'ok'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


