from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.models import User
from bookings.models import Booking, Prescription
from core.models import Review
from core.constants import (
    USER_ROLE_DOCTOR, USER_ROLE_PATIENT,
    BOOKING_STATUS_PENDING, BOOKING_STATUS_CONFIRMED,
    BOOKING_STATUS_COMPLETED, BOOKING_STATUS_CANCELLED,
    DAYS_RECENT, DAYS_LAST_WEEK, MONTHS_TREND
)


@staff_member_required
def analytics_dashboard(request):
    """
    Basic analytics dashboard for hospital administrators
    """
    # Date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=DAYS_RECENT)
    last_7_days = today - timedelta(days=DAYS_LAST_WEEK)
    
    # Basic statistics
    total_patients = User.objects.filter(role=USER_ROLE_PATIENT).count()
    total_doctors = User.objects.filter(role=USER_ROLE_DOCTOR).count()
    total_appointments = Booking.objects.count()
    total_prescriptions = Prescription.objects.count()
    
    # Recent statistics
    recent_appointments = Booking.objects.filter(booking_date__gte=last_30_days).count()
    recent_patients = User.objects.filter(role=USER_ROLE_PATIENT, date_joined__gte=last_30_days).count()
    recent_doctors = User.objects.filter(role=USER_ROLE_DOCTOR, date_joined__gte=last_30_days).count()
    
    # Appointment status breakdown
    appointment_stats = Booking.objects.aggregate(
        pending=Count('id', filter=Q(status=BOOKING_STATUS_PENDING)),
        confirmed=Count('id', filter=Q(status=BOOKING_STATUS_CONFIRMED)),
        completed=Count('id', filter=Q(status=BOOKING_STATUS_COMPLETED)),
        cancelled=Count('id', filter=Q(status=BOOKING_STATUS_CANCELLED)),
    )
    
    # Top doctors by appointment count
    top_doctors = User.objects.filter(role=USER_ROLE_DOCTOR).annotate(
        appointment_count=Count('appointments')
    ).order_by('-appointment_count')[:5]
    
    # Doctor specialization distribution
    specialization_stats = User.objects.filter(
        role=USER_ROLE_DOCTOR, 
        profile__specialization__isnull=False
    ).values('profile__specialization').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Monthly appointment trends (last 6 months)
    monthly_trends = []
    for i in range(MONTHS_TREND):
        month_start = today.replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        count = Booking.objects.filter(
            booking_date__gte=month_start,
            booking_date__lt=month_end
        ).count()
        monthly_trends.append({
            'month': month_start.strftime('%B %Y'),
            'count': count
        })
    
    # Average rating
    avg_rating = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'total_prescriptions': total_prescriptions,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
        'recent_doctors': recent_doctors,
        'appointment_stats': appointment_stats,
        'top_doctors': top_doctors,
        'specialization_stats': specialization_stats,
        'monthly_trends': list(reversed(monthly_trends)),
        'avg_rating': round(avg_rating, 1),
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required
def analytics_api(request):
    """
    API endpoint for analytics data (for AJAX requests)
    """
    data_type = request.GET.get('type', 'overview')
    
    if data_type == 'appointments_by_day':
        # Last 7 days appointment data
        data = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Booking.objects.filter(appointment_date=date).count()
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        return JsonResponse({'data': list(reversed(data))})
    
    elif data_type == 'doctor_performance':
        # Doctor performance metrics
        doctors = User.objects.filter(role=USER_ROLE_DOCTOR).annotate(
            appointment_count=Count('appointments'),
            avg_rating=Avg('reviews_received__rating')
        ).order_by('-appointment_count')[:10]
        
        data = []
        for doctor in doctors:
            data.append({
                'name': doctor.get_full_name(),
                'appointments': doctor.appointment_count,
                'rating': round(doctor.avg_rating or 0, 1)
            })
        
        return JsonResponse({'data': data})
    
    return JsonResponse({'error': 'Invalid data type'}, status=400)