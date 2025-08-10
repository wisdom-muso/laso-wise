from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from bookings.models import Booking, Prescription
from doctors.models import (
    Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, TimeRange
)
from mixins.custom_mixins import DoctorRequiredMixin


class DoctorDashboardAPI(DoctorRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        total_patients = (
            Booking.objects.filter(doctor=request.user).values("patient").distinct().count()
        )
        today_patients = Booking.objects.filter(doctor=request.user, appointment_date=today).count()
        total_appointments = Booking.objects.filter(doctor=request.user).count()

        upcoming = (
            Booking.objects.select_related("patient", "patient__profile")
            .filter(
                doctor=request.user,
                appointment_date__gte=today,
                status__in=["pending", "confirmed"],
            )
            .order_by("appointment_date", "appointment_time")[:10]
        )
        upcoming_data = [
            {
                "id": b.id,
                "patient": {
                    "id": b.patient.id,
                    "name": b.patient.get_full_name(),
                    "age": getattr(b.patient.profile, "age", None),
                    "image": b.patient.profile.image if hasattr(b.patient, "profile") else None,
                },
                "appointment_date": b.appointment_date,
                "appointment_time": b.appointment_time,
                "status": b.status,
                "amount": getattr(b.doctor.profile, "price_per_consultation", None),
            }
            for b in upcoming
        ]

        recent_prescriptions = (
            Prescription.objects.select_related("patient", "patient__profile")
            .filter(doctor=request.user)
            .order_by("-created_at")[:10]
        )
        rx_data = [
            {
                "id": p.id,
                "date": p.created_at,
                "patient": {
                    "id": p.patient.id,
                    "name": p.patient.get_full_name(),
                    "age": getattr(p.patient.profile, "age", None),
                    "image": p.patient.profile.image if hasattr(p.patient, "profile") else None,
                },
                "diagnosis": p.diagnosis,
            }
            for p in recent_prescriptions
        ]

        return Response(
            {
                "stats": {
                    "totalPatients": total_patients,
                    "todayPatients": today_patients,
                    "totalAppointments": total_appointments,
                },
                "upcomingAppointments": upcoming_data,
                "recentPrescriptions": rx_data,
            }
        )


class DoctorAppointmentActionAPI(DoctorRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action):
        appointment = get_object_or_404(
            Booking, pk=pk, doctor=request.user, status__in=["pending", "confirmed"]
        )
        if action == "accept":
            appointment.status = "confirmed"
        elif action == "cancel":
            appointment.status = "cancelled"
        elif action == "completed":
            appointment.status = "completed"
        else:
            return Response({"detail": "Invalid action"}, status=400)
        appointment.save()
        return Response({"ok": True, "status": appointment.status})


class DoctorScheduleAPI(DoctorRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return current schedule
        def serialize_day(day_model):
            day = day_model.objects.filter(user=request.user).first()
            if not day:
                return []
            return [{"start": tr.start, "end": tr.end, "slots_per_hour": tr.slots_per_hour} for tr in day.time_range.all()]

        return Response({
            'sunday': serialize_day(Sunday),
            'monday': serialize_day(Monday),
            'tuesday': serialize_day(Tuesday),
            'wednesday': serialize_day(Wednesday),
            'thursday': serialize_day(Thursday),
            'friday': serialize_day(Friday),
            'saturday': serialize_day(Saturday),
        })

    def post(self, request):
        # Update schedule from JSON
        payload = request.data or {}
        days = [Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday]
        for idx, model in enumerate(days):
            key = model.__name__.lower()
            blocks = payload.get(key, [])
            day_obj, _ = model.objects.get_or_create(user=request.user)
            day_obj.time_range.clear()
            for b in blocks:
                start = b.get('start')
                end = b.get('end')
                slots = b.get('slots_per_hour', 4)
                if start and end:
                    tr, _ = TimeRange.objects.get_or_create(start=start, end=end, defaults={'slots_per_hour': slots})
                    tr.slots_per_hour = slots
                    tr.save()
                    day_obj.time_range.add(tr)
        return Response({'ok': True})


