from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView, View, CreateView, ListView
from django.views.generic.base import TemplateView
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.models import User
from bookings.models import Booking, Prescription, ProgressNote
from mixins.custom_mixins import PatientRequiredMixin
from patients.forms import PatientProfileForm, ChangePasswordForm, ReviewForm
from core.models import Review
from vitals.models import VitalRecord


class PatientDashboardView(PatientRequiredMixin, TemplateView):
    template_name = "patients/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Get all appointments
        appointments = Booking.objects.select_related("doctor", "doctor__profile").filter(patient=user)
        context["appointments"] = appointments.order_by("-appointment_date", "-appointment_time")[:10]  # Limit to 10 most recent
        
        # Get upcoming appointments
        upcoming_appointments = appointments.filter(
            appointment_date__gte=today,
            status__in=["pending", "confirmed"]
        ).order_by("appointment_date", "appointment_time")
        context["upcoming_appointments"] = upcoming_appointments[:5]
        
        # Get recent prescriptions
        prescriptions = Prescription.objects.filter(patient=user).select_related("doctor", "doctor__profile")
        context["prescriptions"] = prescriptions.order_by("-created_at")[:10]
        
        # Dashboard statistics
        context["upcoming_appointments_count"] = upcoming_appointments.count()
        context["prescriptions_count"] = prescriptions.count()
        context["doctors_consulted_count"] = appointments.values('doctor').distinct().count()
        
        # Calculate a simple health score based on recent activity
        recent_appointments = appointments.filter(
            appointment_date__gte=today - timedelta(days=90),
            status="completed"
        ).count()
        
        # Simple health score calculation (0-100)
        health_score = min(100, max(20, 50 + (recent_appointments * 10)))
        context["health_score"] = health_score
        
        # Get recent vitals if available
        try:
            from vitals.models import VitalRecord
            recent_vitals = VitalRecord.objects.filter(
                patient=user
            ).select_related("category").order_by("-recorded_at")[:5]
            context["recent_vitals"] = recent_vitals
        except:
            context["recent_vitals"] = []
        
        # Get EHR record if available
        try:
            from core.models import EHRRecord
            ehr_record, created = EHRRecord.objects.get_or_create(patient=user)
            context["ehr_record"] = ehr_record
        except:
            context["ehr_record"] = None
            
        # Next appointment
        next_appointment = upcoming_appointments.first()
        context["next_appointment"] = next_appointment
        
        # Recent activity count
        context["recent_activity_count"] = (
            appointments.filter(appointment_date__gte=today - timedelta(days=30)).count() +
            prescriptions.filter(created_at__gte=today - timedelta(days=30)).count()
        )
        
        # Current date
        context["today"] = today
        
        return context


class PatientProfileUpdateView(PatientRequiredMixin, UpdateView):
    model = User
    template_name = "patients/profile-setting.html"
    success_url = reverse_lazy("patients:profile-setting")
    form_class = PatientProfileForm

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = form.save(commit=False)
        profile = user.profile

        # Handle profile image upload
        if self.request.FILES.get("avatar"):
            profile.image = self.request.FILES["avatar"]

        # Update user fields from form
        user.first_name = form.cleaned_data.get('first_name', user.first_name)
        user.last_name = form.cleaned_data.get('last_name', user.last_name)
        user.email = form.cleaned_data.get('email', user.email)

        # Update profile fields
        profile_fields = [
            "dob",
            "blood_group", 
            "gender",
            "phone",
            "medical_conditions",
            "allergies",
            "address",
            "city",
            "state",
            "postal_code",
            "country",
        ]

        for field in profile_fields:
            value = form.cleaned_data.get(field) or self.request.POST.get(field)
            if value is not None:
                setattr(profile, field, value)

        # Save both user and profile
        user.save()
        profile.save()

        messages.success(self.request, "Profile updated successfully")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blood_group_choices"] = [
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ]
        return context


class AppointmentDetailView(DetailView):
    model = Booking
    template_name = "patients/appointment-detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return Booking.objects.select_related(
            "doctor", "doctor__profile", "patient", "patient__profile"
        ).filter(patient=self.request.user)


class AppointmentCancelView(View):
    def post(self, request, pk):
        appointment = get_object_or_404(
            Booking,
            pk=pk,
            patient=request.user,
            status__in=["pending", "confirmed"],
        )

        appointment.status = "cancelled"
        appointment.save()

        messages.success(request, "Appointment cancelled successfully")
        return redirect("patients:dashboard")


class AppointmentPrintView(DetailView):
    model = Booking
    template_name = "patients/appointment-print.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return Booking.objects.select_related(
            "doctor", "doctor__profile", "patient", "patient__profile"
        ).filter(patient=self.request.user)

    def render_to_response(self, context):
        html_string = render_to_string(
            self.template_name, context, request=self.request
        )
        return HttpResponse(html_string)


class ChangePasswordView(PatientRequiredMixin, View):
    template_name = "patients/change-password.html"

    def get(self, request):
        form = ChangePasswordForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user

            if user.check_password(form.cleaned_data["old_password"]):
                user.set_password(form.cleaned_data["new_password"])
                user.save()

                # Update session to prevent logout
                update_session_auth_hash(request, user)

                messages.success(request, "Password changed successfully")
                return redirect("patients:dashboard")
            else:
                messages.error(request, "Current password is incorrect")

        return render(request, self.template_name, {"form": form})


class AddReviewView(PatientRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = "patients/add_review.html"

    def form_valid(self, form):
        booking_id = self.kwargs.get("booking_id")
        booking = get_object_or_404(
            Booking, id=booking_id, patient=self.request.user
        )

        if booking.status != "completed":
            messages.error(
                self.request, "You can only review completed appointments."
            )
            return redirect("patients:appointment-detail", pk=booking_id)

        if Review.objects.filter(booking=booking).exists():
            messages.error(
                self.request, "You have already reviewed this appointment."
            )
            return redirect("patients:appointment-detail", pk=booking_id)

        form.instance.patient = self.request.user
        form.instance.doctor = booking.doctor
        form.instance.booking = booking
        messages.success(self.request, "Thank you for your review!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "patients:appointment-detail",
            kwargs={"pk": self.kwargs["booking_id"]},
        )


class PrescriptionListView(PatientRequiredMixin, ListView):
    model = Prescription
    template_name = "patients/prescriptions.html"
    context_object_name = "prescriptions"
    
    def get_queryset(self):
        return Prescription.objects.filter(patient=self.request.user).select_related(
            "doctor", "doctor__profile"
        ).order_by("-created_at")


class PrescriptionDetailView(PatientRequiredMixin, DetailView):
    model = Prescription
    template_name = "patients/prescription_detail.html"
    context_object_name = "prescription"
    
    def get_queryset(self):
        return Prescription.objects.filter(patient=self.request.user).select_related(
            "doctor", "doctor__profile"
        )


class PrescriptionPrintView(PatientRequiredMixin, DetailView):
    model = Prescription
    template_name = "patients/prescription_print.html"
    context_object_name = "prescription"
    
    def get_queryset(self):
        return Prescription.objects.filter(patient=self.request.user).select_related(
            "doctor", "doctor__profile", "patient"
        )


class MedicalRecordsView(PatientRequiredMixin, TemplateView):
    template_name = "patients/medical_records.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create EHR record
        try:
            from core.models import EHRRecord, SoapNote
            ehr_record, created = EHRRecord.objects.get_or_create(patient=user)
            context["ehr_record"] = ehr_record
        except:
            context["ehr_record"] = None
        
        # Get progress notes (which are like SOAP notes)
        context["progress_notes"] = ProgressNote.objects.filter(
            patient=user, is_private=False
        ).select_related("doctor", "doctor__profile").order_by("-created_at")
        
        # Get SOAP notes
        try:
            context["soap_notes"] = SoapNote.objects.filter(
                patient=user
            ).select_related("created_by", "appointment").order_by("-created_at")
        except:
            context["soap_notes"] = []
        
        # Get prescriptions
        context["prescriptions"] = Prescription.objects.filter(
            patient=user
        ).select_related("doctor", "doctor__profile").order_by("-created_at")
        
        # Get recent vitals
        try:
            context["recent_vitals"] = VitalRecord.objects.filter(
                patient=user
            ).select_related("category").order_by("-recorded_at")[:5]
        except:
            context["recent_vitals"] = []
            
        return context
