from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from bookings.models import Booking, Prescription
from mixins.custom_mixins import PatientRequiredMixin


class PatientDashboardAPI(PatientRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        appointments_qs = Booking.objects.select_related("doctor", "doctor__profile").filter(patient=user)

        upcoming_count = appointments_qs.filter(
            appointment_date__gte=today, status__in=["pending", "confirmed"]
        ).count()

        prescriptions_count = Prescription.objects.filter(patient=user).count()
        doctors_consulted = appointments_qs.values("doctor").distinct().count()

        recent_appointments = (
            appointments_qs.order_by("-appointment_date", "-appointment_time")[:10]
        )
        appointments = [
            {
                "id": appt.id,
                "doctor": {
                    "id": appt.doctor.id,
                    "name": appt.doctor.get_full_name(),
                    "specialization": getattr(appt.doctor.profile, "specialization", None),
                    "image": appt.doctor.profile.image if hasattr(appt.doctor, "profile") else None,
                },
                "appointment_date": appt.appointment_date,
                "appointment_time": appt.appointment_time,
                "booking_date": appt.booking_date,
                "status": appt.status,
            }
            for appt in recent_appointments
        ]

        # Simple health score calculation (0-100)
        recent_completed = appointments_qs.filter(
            appointment_date__gte=today - timedelta(days=90), status="completed"
        ).count()
        health_score = min(100, max(20, 50 + (recent_completed * 10)))

        return Response(
            {
                "stats": {
                    "upcomingAppointments": upcoming_count,
                    "prescriptions": prescriptions_count,
                    "doctorsConsulted": doctors_consulted,
                    "healthScore": health_score,
                },
                "appointments": appointments,
            }
        )


class PatientAppointmentsAPI(PatientRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = (
            Booking.objects.select_related("doctor", "doctor__profile")
            .filter(patient=user)
            .order_by("-appointment_date", "-appointment_time")
        )
        limit = int(request.GET.get("limit", 20))
        data = [
            {
                "id": appt.id,
                "doctor": {
                    "id": appt.doctor.id,
                    "name": appt.doctor.get_full_name(),
                    "specialization": getattr(appt.doctor.profile, "specialization", None),
                    "image": appt.doctor.profile.image if hasattr(appt.doctor, "profile") else None,
                },
                "appointment_date": appt.appointment_date,
                "appointment_time": appt.appointment_time,
                "booking_date": appt.booking_date,
                "status": appt.status,
            }
            for appt in qs[:limit]
        ]
        return Response({"results": data})


class PatientPrescriptionsAPI(PatientRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Prescription.objects.select_related("doctor", "doctor__profile")
            .filter(patient=request.user)
            .order_by("-created_at")
        )
        limit = int(request.GET.get("limit", 20))
        data = [
            {
                "id": p.id,
                "date": p.created_at,
                "doctor": {
                    "id": p.doctor.id,
                    "name": p.doctor.get_full_name(),
                    "specialization": getattr(p.doctor.profile, "specialization", None),
                    "image": p.doctor.profile.image if hasattr(p.doctor, "profile") else None,
                },
                "diagnosis": p.diagnosis,
            }
            for p in qs[:limit]
        ]
        return Response({"results": data})


class PatientAppointmentCancelAPI(PatientRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appt = Booking.objects.filter(
            id=pk, patient=request.user, status__in=["pending", "confirmed"]
        ).first()
        if not appt:
            return Response({"detail": "Appointment not found or cannot cancel"}, status=404)
        appt.status = "cancelled"
        appt.save()
        return Response({"ok": True, "status": appt.status})





