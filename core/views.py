from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView, TemplateView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json

from .forms import (
    LoginForm, PatientRegistrationForm, AppointmentForm, 
    TreatmentForm, PrescriptionFormSet, DoctorCreationForm, DoctorUpdateForm,
    ProfileSettingsForm
)
from appointments.models import Appointment
from treatments.models import Treatment, Prescription
from treatments.models_vitals import VitalSign, VitalSignAlert
from telemedicine.models import MessageThread, DoctorPatientMessage, TeleMedicineConsultation
from .analytics import DashboardAnalytics

User = get_user_model()

# Create your views here.

# Home Page
class HomeView(TemplateView):
    """
    Home page view
    """
    template_name = 'core/index.html'

# Dashboard
@login_required
def dashboard(request):
    """
    Provides dashboard view based on user role
    """
    user = request.user
    context = {'user': user}
    
    if user.is_patient():
        # Patient dashboard
        upcoming_appointments = Appointment.objects.filter(
            patient=user,
            date__gte=timezone.now().date(),
            status='planned'
        ).order_by('date', 'time')
        
        recent_treatments = Treatment.objects.filter(
            appointment__in=Appointment.objects.filter(patient=user)
        ).order_by('-created_at')[:5]
        
        # Vitals data
        latest_vital = VitalSign.objects.filter(patient=user).first()
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_vitals = VitalSign.objects.filter(
            patient=user,
            recorded_at__gte=thirty_days_ago
        ).order_by('-recorded_at')[:10]
        
        # Calculate vitals statistics
        vitals_stats = recent_vitals.aggregate(
            avg_systolic=Avg('systolic_bp'),
            avg_diastolic=Avg('diastolic_bp'),
            avg_heart_rate=Avg('heart_rate'),
            max_systolic=Max('systolic_bp'),
            min_systolic=Min('systolic_bp'),
        )
        
        # Get active vitals alerts
        active_alerts = VitalSignAlert.objects.filter(
            vital_sign__patient=user,
            status='active'
        ).order_by('-created_at')
        
        # Prepare chart data for vitals
        chart_data = {
            'dates': [v.recorded_at.strftime('%Y-%m-%d') for v in recent_vitals],
            'systolic': [v.systolic_bp for v in recent_vitals],
            'diastolic': [v.diastolic_bp for v in recent_vitals],
            'heart_rate': [v.heart_rate for v in recent_vitals],
        }
        
        # Enhanced vitals data for the new design
        vitals_enhanced_data = {}
        if latest_vital:
            vitals_enhanced_data = {
                'risk_percentage': latest_vital.get_risk_percentage(),
                'health_assessment_message': latest_vital.get_health_assessment_message(),
                'risk_trend': latest_vital.get_risk_trend(),
                'risk_level': latest_vital.calculate_risk_level(),
                'assessment_date': latest_vital.recorded_at.strftime('%B %d, %Y'),
            }
        
        # Messaging data
        message_threads = MessageThread.objects.filter(
            patient=user,
            is_active=True
        ).select_related('doctor')
        
        # Get unread message count
        total_unread_messages = sum(thread.patient_unread_count for thread in message_threads)
        
        # Active consultations
        active_consultations = TeleMedicineConsultation.objects.filter(
            appointment__patient=user,
            status='in_progress'
        ).count()
        
        context.update({
            'upcoming_appointments': upcoming_appointments,
            'recent_treatments': recent_treatments,
            # Vitals data
            'latest_vital': latest_vital,
            'recent_vitals': recent_vitals,
            'vitals_stats': vitals_stats,
            'active_alerts': active_alerts,
            'chart_data': chart_data,
            'vitals_enhanced_data': vitals_enhanced_data,
            # Messaging data
            'message_threads': message_threads,
            'total_unread_messages': total_unread_messages,
            'active_consultations': active_consultations,
        })
        return render(request, 'core/patient_dashboard.html', context)
    
    elif user.is_doctor():
        # Doctor dashboard
        today_appointments = Appointment.objects.filter(
            doctor=user,
            date=timezone.now().date(),
            status='planned'
        ).order_by('time')
        
        upcoming_appointments = Appointment.objects.filter(
            doctor=user,
            date__gt=timezone.now().date(),
            status='planned'
        ).order_by('date', 'time')[:5]
        
        recent_treatments = Treatment.objects.filter(
            appointment__in=Appointment.objects.filter(doctor=user)
        ).order_by('-created_at')[:5]
        
        # Total patient count
        # Get all appointments for this doctor
        doctor_appointments = Appointment.objects.filter(doctor=user)
        # Then get all patients from those appointments
        total_patients = User.objects.filter(
            user_type='patient',
            patient_appointments__in=doctor_appointments
        ).distinct().count()
        
        # Total treatment count
        total_treatments = Treatment.objects.filter(
            appointment__in=doctor_appointments
        ).count()
        
        # Weekly appointment statistics
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        weekly_appointments = []
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            count = Appointment.objects.filter(doctor=user, date=day).count()
            weekly_appointments.append(count)
        
        # Patient age demographics
        from django.db.models import Count, Case, When, IntegerField
        from datetime import date
        
        age_demographics = [0, 0, 0, 0, 0]  # 0-18, 19-30, 31-45, 46-60, 60+
        
        # Get all patients who have appointments with this doctor
        doctor_appointments = Appointment.objects.filter(doctor=user)
        patients = User.objects.filter(
            user_type='patient',
            patient_appointments__in=doctor_appointments,
            date_of_birth__isnull=False
        ).distinct()
        
        for patient in patients:
            age = (date.today() - patient.date_of_birth).days // 365
            if age <= 18:
                age_demographics[0] += 1
            elif age <= 30:
                age_demographics[1] += 1
            elif age <= 45:
                age_demographics[2] += 1
            elif age <= 60:
                age_demographics[3] += 1
            else:
                age_demographics[4] += 1
        
        # Most common diagnoses
        from django.db.models import Count
        doctor_appointments = Appointment.objects.filter(doctor=user)
        common_diagnoses_data = Treatment.objects.filter(
            appointment__in=doctor_appointments
        ).values('diagnosis').annotate(
            count=Count('diagnosis')
        ).order_by('-count')[:5]
        
        common_diagnoses = []
        for item in common_diagnoses_data:
            diagnosis = item['diagnosis']
            if len(diagnosis) > 20:
                diagnosis = diagnosis[:20] + "..."
            common_diagnoses.append({
                'name': diagnosis,
                'count': item['count']
            })
        
        context.update({
            'today_appointments': today_appointments,
            'upcoming_appointments': upcoming_appointments,
            'recent_treatments': recent_treatments,
            'total_patients': total_patients,
            'total_treatments': total_treatments,
            'weekly_appointments': weekly_appointments,
            'age_demographics': age_demographics,
            'common_diagnoses': common_diagnoses,
        })
        return render(request, 'core/doctor_dashboard.html', context)
    
    elif user.is_receptionist():
        # Receptionist dashboard
        today_appointments = Appointment.objects.filter(
            date=timezone.now().date()
        ).order_by('time')
        
        recent_patients = User.objects.filter(
            user_type='patient'
        ).order_by('-date_joined')[:5]
        
        context.update({
            'today_appointments': today_appointments,
            'recent_patients': recent_patients,
        })
        return render(request, 'core/receptionist_dashboard.html', context)
    
    elif user.is_admin_user() or user.is_superuser:
        # Admin dashboard
        total_patients = User.objects.filter(user_type='patient').count()
        total_doctors = User.objects.filter(user_type='doctor').count()
        total_appointments = Appointment.objects.count()
        total_treatments = Treatment.objects.count()
        
        context.update({
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_appointments': total_appointments,
            'total_treatments': total_treatments,
        })
        return render(request, 'core/admin_dashboard.html', context)
    
    # Redirect to general dashboard by default
    return render(request, 'core/dashboard.html', context)

# Patient Registration
class PatientRegistrationView(CreateView):
    """
    Patient registration view for creating new patient accounts
    """
    template_name = 'core/patient_registration.html'
    form_class = PatientRegistrationForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        messages.success(self.request, _('Patient registration completed successfully. You can now log in with your credentials.'))
        response = super().form_valid(form)
        return response
    
    def form_invalid(self, form):
        # Create detailed error message
        error_messages = []
        for field, errors in form.errors.items():
            if field == '__all__':
                error_messages.extend(errors)
            else:
                field_label = form.fields[field].label or field.replace('_', ' ').title()
                for error in errors:
                    error_messages.append(f"{field_label}: {error}")
        
        if error_messages:
            detailed_error = "Registration failed with the following errors: " + "; ".join(error_messages)
            messages.error(self.request, detailed_error)
        else:
            messages.error(self.request, _('Registration Failed. Please check the form for errors and try again.'))
        
        return super().form_invalid(form)

# Appointment Views
class AppointmentListView(LoginRequiredMixin, ListView):
    """
    Appointment list view
    """
    model = Appointment
    template_name = 'core/appointment_list.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtering
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if user.is_patient():
            queryset = queryset.filter(patient=user)
        elif user.is_doctor():
            queryset = queryset.filter(doctor=user)
        
        if status:
            queryset = queryset.filter(status=status)
            
        if search:
            if user.is_patient():
                queryset = queryset.filter(
                    Q(doctor__first_name__icontains=search) |
                    Q(doctor__last_name__icontains=search) |
                    Q(description__icontains=search)
                )
            elif user.is_doctor() or user.is_receptionist() or user.is_admin_user():
                queryset = queryset.filter(
                    Q(patient__first_name__icontains=search) |
                    Q(patient__last_name__icontains=search) |
                    Q(description__icontains=search)
                )
        
        return queryset.order_by('-date', '-time')

class AppointmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Appointment creation view
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'core/appointment_form.html'
    success_url = reverse_lazy('core:appointment-list')
    
    def test_func(self):
        # All users can create appointments
        return True
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        # If doctor ID is taken from URL, automatically select doctor
        doctor_id = self.request.GET.get('doctor')
        if doctor_id:
            initial['doctor'] = doctor_id
        
        # If patient ID is taken from URL, automatically select patient
        patient_id = self.request.GET.get('patient')
        if patient_id:
            initial['patient'] = patient_id
        elif self.request.user.is_patient():
            initial['patient'] = self.request.user.id
            
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Appointment created successfully.'))
        return response

class AppointmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Appointment update view
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'core/appointment_form.html'
    success_url = reverse_lazy('core:appointment-list')
    
    def test_func(self):
        appointment = self.get_object()
        user = self.request.user
        # Doctors and receptionists can update their own appointments
        if user.is_doctor():
            return appointment.doctor == user
        return user.is_receptionist() or user.is_admin_user()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Appointment updated successfully.'))
        return response

class AppointmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Appointment detail view
    """
    model = Appointment
    template_name = 'core/appointment_detail.html'
    context_object_name = 'appointment'
    
    def test_func(self):
        appointment = self.get_object()
        user = self.request.user
        # Doctor and patient can only view their own appointments
        if user.is_patient():
            return appointment.patient == user
        elif user.is_doctor():
            return appointment.doctor == user
        return user.is_receptionist() or user.is_admin_user()

class AppointmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Appointment deletion view
    """
    model = Appointment
    template_name = 'core/appointment_confirm_delete.html'
    success_url = reverse_lazy('core:appointment-list')
    
    def test_func(self):
        # Only receptionists and admins can delete appointments
        return self.request.user.is_receptionist() or self.request.user.is_admin_user()
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, _('Appointment deleted successfully.'))
        return response

# Treatment Views
class TreatmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Treatment creation view
    """
    model = Treatment
    form_class = TreatmentForm
    template_name = 'core/treatment_form.html'
    success_url = reverse_lazy('core:appointment-list')
    
    def test_func(self):
        # Only doctors can create treatments
        return self.request.user.is_doctor()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['prescription_formset'] = PrescriptionFormSet(self.request.POST)
        else:
            context['prescription_formset'] = PrescriptionFormSet()
        
        # Add appointment information
        appointment_id = self.kwargs.get('appointment_id')
        if appointment_id:
            context['appointment'] = get_object_or_404(Appointment, id=appointment_id)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        prescription_formset = context['prescription_formset']
        
        # Associate with appointment
        appointment_id = self.kwargs.get('appointment_id')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Doctor can only add treatment to their own appointments
        if appointment.doctor != self.request.user:
            messages.error(self.request, _('You cannot add treatment for this appointment.'))
            return redirect('appointment-list')
        
        # Mark appointment status as completed
        appointment.status = 'completed'
        appointment.save()
        
        # Save treatment and prescriptions
        if prescription_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.appointment = appointment
            self.object.save()
            
            prescription_formset.instance = self.object
            prescription_formset.save()
            
            messages.success(self.request, _('Treatment and prescriptions saved successfully.'))
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class TreatmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Treatment update view
    """
    model = Treatment
    form_class = TreatmentForm
    template_name = 'core/treatment_form.html'
    success_url = reverse_lazy('core:appointment-list')
    
    def test_func(self):
        treatment = self.get_object()
        # Only the doctor who created the treatment can update it
        return self.request.user.is_doctor() and treatment.appointment.doctor == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['prescription_formset'] = PrescriptionFormSet(self.request.POST, instance=self.object)
        else:
            context['prescription_formset'] = PrescriptionFormSet(instance=self.object)
        
        context['appointment'] = self.object.appointment
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        prescription_formset = context['prescription_formset']
        
        if prescription_formset.is_valid():
            self.object = form.save()
            prescription_formset.instance = self.object
            prescription_formset.save()
            
            messages.success(self.request, _('Treatment and prescriptions updated successfully.'))
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class TreatmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Treatment detail view
    """
    model = Treatment
    template_name = 'core/treatment_detail.html'
    context_object_name = 'treatment'
    
    def test_func(self):
        treatment = self.get_object()
        user = self.request.user
        # Patient and doctor can only view their own treatments
        if user.is_patient():
            return treatment.appointment.patient == user
        elif user.is_doctor():
            return treatment.appointment.doctor == user
        return user.is_receptionist() or user.is_admin_user()

# Patient Views
class PatientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Patient list view
    """
    model = User
    template_name = 'core/patient_list.html'
    context_object_name = 'patients'
    
    def test_func(self):
        # Only doctors, receptionists and admins can view patient list
        user = self.request.user
        return user.is_doctor() or user.is_receptionist() or user.is_admin_user()
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='patient')
        
        # Doctors can only see patients who have appointments with them
        if self.request.user.is_doctor():
            doctor = self.request.user
            patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True)
            queryset = queryset.filter(id__in=patient_ids).distinct()
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('first_name', 'last_name')

class PatientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Patient detail view
    """
    model = User
    template_name = 'core/patient_detail.html'
    context_object_name = 'patient'
    
    def test_func(self):
        patient = self.get_object()
        user = self.request.user
        
        # Patients can only view their own profiles
        if user.is_patient():
            return patient == user
        
        # Doctors can only view patients who have appointments with them
        if user.is_doctor():
            return Appointment.objects.filter(doctor=user, patient=patient).exists()
            
        # Receptionists and admins can view all patients
        return user.is_receptionist() or user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        
        # Patient appointments
        appointments = Appointment.objects.filter(patient=patient).order_by('-date', '-time')
        
        # Patient treatments
        patient_appointments = Appointment.objects.filter(patient=patient)
        treatments = Treatment.objects.filter(appointment__in=patient_appointments).order_by('-created_at')
        
        context.update({
            'appointments': appointments,
            'treatments': treatments
        })
        
        return context

# Doctor Views
class DoctorListView(LoginRequiredMixin, ListView):
    """
    Doctor list view
    """
    model = User
    template_name = 'core/doctor_list.html'
    context_object_name = 'doctors'
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='doctor')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(specialization__icontains=search)
            )
        
        return queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Find currently available doctors
        from appointments.models_availability import DoctorAvailability, DoctorTimeOff
        from datetime import datetime
        
        now = datetime.now()
        current_weekday = now.weekday()  # 0 = Pazartesi, 6 = Pazar
        current_time = now.time()
        
        # Doctors working today
        working_doctors = User.objects.filter(
            user_type='doctor',
            availabilities__weekday=current_weekday,
            availabilities__start_time__lte=current_time,
            availabilities__end_time__gte=current_time,
            availabilities__is_active=True
        ).distinct()
        
        # Exclude doctors on leave today
        today = now.date()
        on_leave_doctor_ids = DoctorTimeOff.objects.filter(
            start_date__lte=today,
            end_date__gte=today
        ).values_list('doctor_id', flat=True)
        
        available_doctors = working_doctors.exclude(id__in=on_leave_doctor_ids)
        
        context['available_doctors'] = available_doctors
        context['current_time'] = now
        
        return context

class DoctorCreationView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Doctor creation view
    """
    model = User
    form_class = DoctorCreationForm
    template_name = 'core/doctor_form.html'
    success_url = reverse_lazy('doctor-list')
    
    def test_func(self):
        # Only admin users can add doctors
        return self.request.user.is_admin_user() or self.request.user.is_superuser
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Doctor account created successfully.'))
        return response

class DoctorDetailView(LoginRequiredMixin, DetailView):
    """
    Doctor detail view
    """
    model = User
    template_name = 'core/doctor_detail.html'
    context_object_name = 'doctor'
    
    def get_queryset(self):
        return User.objects.filter(user_type='doctor')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.get_object()
        # Additional data can be added as needed
        return context

class DoctorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Doctor update view
    """
    model = User
    form_class = DoctorUpdateForm
    template_name = 'core/doctor_form.html'
    success_url = reverse_lazy('doctor-list')
    
    def test_func(self):
        # Only admin users can update doctor information
        return self.request.user.is_admin_user() or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Doctor information updated successfully.'))
        return response

# Analytics Dashboard View
@login_required
def analytics_dashboard(request):
    """
    Advanced analytics dashboard view
    """
    # Access control based on user role
    if not (request.user.is_doctor() or request.user.is_admin_user()):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('home')
    
    # Prepare analytics data
    analytics = DashboardAnalytics(user=request.user)
    dashboard_data = analytics.get_comprehensive_dashboard_data()
    
    context = {
        'dashboard_data': dashboard_data
    }
    
    return render(request, 'dashboards/analytics_dashboard.html', context)

# AI Assistant View
@login_required
def ai_assistant(request):
    """
    AI Health Assistant view
    """
    context = {
        'title': _('AI Health Assistant'),
        'current_time': timezone.now()
    }
    
    return render(request, 'core/ai_assistant.html', context)

@login_required
@require_http_methods(["POST"])
def ai_chat(request):
    """
    AI Chat endpoint for processing user messages
    """
    try:
        import json
        from .ai_service import ai_service
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
        else:
            message = request.POST.get('message', '').strip()
            session_id = request.POST.get('session_id')
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'No message provided'
            })
        
        # Use the enhanced AI service
        result = ai_service.chat(request.user, message, session_id)
        
        return JsonResponse({
            'success': result['success'],
            'response': result.get('response', ''),
            'session_id': result.get('session_id'),
            'conversation_id': result.get('conversation_id'),
            'tokens_used': result.get('tokens_used', 0),
            'response_time': result.get('response_time', 0),
            'error': result.get('error'),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred processing your request',
            'response': 'I apologize, but I encountered an error. Please try again or contact support if the issue persists.'
        })

class ProfileSettingsView(LoginRequiredMixin, UpdateView):
    """
    Profile settings view for updating user profile and theme preferences.
    """
    model = User
    form_class = ProfileSettingsForm
    template_name = 'core/profile_settings.html'
    success_url = reverse_lazy('core:profile-settings')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Profile settings updated successfully!'))
        return super().form_valid(form)


class LoginSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Admin view to display login sessions
    """
    template_name = 'core/login_sessions.html'
    context_object_name = 'sessions'
    paginate_by = 50
    
    def test_func(self):
        """Only allow admin users to access this view"""
        return self.request.user.is_admin_user() or self.request.user.is_superuser
    
    def get_queryset(self):
        from .models_sessions import LoginSession
        queryset = LoginSession.objects.select_related('user').order_by('-login_time')
        
        # Filter by user type if specified
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user__user_type=user_type)
        
        # Filter by active status if specified
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Search by user name or IP
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(ip_address__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models_sessions import LoginSession
        
        # Add summary statistics
        context['total_sessions'] = LoginSession.objects.count()
        context['active_sessions'] = LoginSession.objects.filter(is_active=True).count()
        context['today_sessions'] = LoginSession.objects.filter(
            login_time__date=timezone.now().date()
        ).count()
        
        # Add filter options
        context['user_types'] = [
            ('patient', _('Patient')),
            ('doctor', _('Doctor')),
            ('receptionist', _('Receptionist')),
            ('admin', _('Admin')),
        ]
        
        # Preserve current filters
        context['current_user_type'] = self.request.GET.get('user_type', '')
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        return context
