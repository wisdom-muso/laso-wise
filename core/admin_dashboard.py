from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from appointments.models import Appointment
from treatments.models import Treatment
from core.models_sessions import LoginSession
import json

User = get_user_model()

@staff_member_required
def admin_dashboard(request):
    """
    Beautiful admin dashboard with comprehensive metrics and charts
    """
    # Get current date and time ranges
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    # User Statistics
    total_users = User.objects.count()
    total_patients = User.objects.filter(user_type='patient').count()
    total_doctors = User.objects.filter(user_type='doctor').count()
    total_receptionists = User.objects.filter(user_type='receptionist').count()
    total_admins = User.objects.filter(user_type='admin').count()
    
    # New users this month
    new_users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
    new_users_last_month = User.objects.filter(
        date_joined__gte=month_ago - timedelta(days=30),
        date_joined__lt=month_ago
    ).count()
    
    # Calculate growth percentage
    if new_users_last_month > 0:
        user_growth_percentage = ((new_users_this_month - new_users_last_month) / new_users_last_month) * 100
    else:
        user_growth_percentage = 100 if new_users_this_month > 0 else 0
    
    # Active users (logged in within last 30 days)
    active_users = LoginSession.objects.filter(
        login_time__gte=month_ago
    ).values('user').distinct().count()
    
    # User engagement rate
    engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
    
    # Appointment Statistics
    total_appointments = Appointment.objects.count()
    appointments_today = Appointment.objects.filter(date=today).count()
    appointments_this_week = Appointment.objects.filter(date__gte=week_ago).count()
    appointments_this_month = Appointment.objects.filter(date__gte=month_ago).count()
    
    # Appointment status breakdown
    appointment_status = Appointment.objects.values('status').annotate(count=Count('id'))
    
    # Treatment Statistics
    total_treatments = Treatment.objects.count()
    treatments_this_month = Treatment.objects.filter(created_at__gte=month_ago).count()
    
    # User registration trend (last 12 months)
    user_trend_data = []
    for i in range(12):
        month_start = (now - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_users = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        
        user_trend_data.append({
            'month': month_start.strftime('%b %Y'),
            'users': month_users
        })
    
    user_trend_data.reverse()  # Show oldest to newest
    
    # Daily active users (last 30 days)
    daily_active_data = []
    for i in range(30):
        day = today - timedelta(days=i)
        active_count = LoginSession.objects.filter(
            login_time__date=day
        ).values('user').distinct().count()
        
        daily_active_data.append({
            'date': day.strftime('%m/%d'),
            'active_users': active_count
        })
    
    daily_active_data.reverse()  # Show oldest to newest
    
    # User type distribution
    user_type_data = [
        {'type': 'Patients', 'count': total_patients, 'color': '#10b981'},
        {'type': 'Doctors', 'count': total_doctors, 'color': '#3b82f6'},
        {'type': 'Receptionists', 'count': total_receptionists, 'color': '#f59e0b'},
        {'type': 'Admins', 'count': total_admins, 'color': '#ef4444'},
    ]
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_appointments = Appointment.objects.order_by('-created_at')[:10]
    recent_treatments = Treatment.objects.order_by('-created_at')[:10]
    
    # System health metrics
    system_health = {
        'database_status': 'healthy',  # You can add actual health checks
        'redis_status': 'healthy',
        'celery_status': 'healthy',
        'disk_usage': 45,  # Percentage
        'memory_usage': 62,  # Percentage
    }
    
    context = {
        # User Statistics
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_receptionists': total_receptionists,
        'total_admins': total_admins,
        'new_users_this_month': new_users_this_month,
        'user_growth_percentage': round(user_growth_percentage, 1),
        'active_users': active_users,
        'engagement_rate': round(engagement_rate, 1),
        
        # Appointment Statistics
        'total_appointments': total_appointments,
        'appointments_today': appointments_today,
        'appointments_this_week': appointments_this_week,
        'appointments_this_month': appointments_this_month,
        'appointment_status': list(appointment_status),
        
        # Treatment Statistics
        'total_treatments': total_treatments,
        'treatments_this_month': treatments_this_month,
        
        # Chart Data (JSON for JavaScript)
        'user_trend_data': json.dumps(user_trend_data),
        'daily_active_data': json.dumps(daily_active_data),
        'user_type_data': json.dumps(user_type_data),
        
        # Recent Activity
        'recent_users': recent_users,
        'recent_appointments': recent_appointments,
        'recent_treatments': recent_treatments,
        
        # System Health
        'system_health': system_health,
        
        # Date ranges for display
        'today': today,
        'week_ago': week_ago,
        'month_ago': month_ago,
    }
    
    return render(request, 'admin/dashboard.html', context)


def admin_dashboard_callback(request, context):
    """
    Django Unfold dashboard callback function
    This integrates our custom dashboard with Django Unfold
    """
    # Get current date and time ranges
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    # User Statistics
    total_users = User.objects.count()
    total_patients = User.objects.filter(user_type='patient').count()
    total_doctors = User.objects.filter(user_type='doctor').count()
    total_receptionists = User.objects.filter(user_type='receptionist').count()
    total_admins = User.objects.filter(user_type='admin').count()
    
    # New users this month
    new_users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
    new_users_last_month = User.objects.filter(
        date_joined__gte=month_ago - timedelta(days=30),
        date_joined__lt=month_ago
    ).count()
    
    # Calculate growth percentage
    if new_users_last_month > 0:
        user_growth_percentage = ((new_users_this_month - new_users_last_month) / new_users_last_month) * 100
    else:
        user_growth_percentage = 100 if new_users_this_month > 0 else 0
    
    # Active users (logged in within last 30 days)
    active_users = LoginSession.objects.filter(
        login_time__gte=month_ago
    ).values('user').distinct().count()
    
    # Appointment Statistics
    total_appointments = Appointment.objects.count()
    appointments_today = Appointment.objects.filter(date=today).count()
    appointments_this_week = Appointment.objects.filter(date__gte=week_ago).count()
    appointments_this_month = Appointment.objects.filter(date__gte=month_ago).count()
    
    # Appointment status breakdown
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
    
    # Treatment Statistics
    total_treatments = Treatment.objects.count()
    treatments_this_month = Treatment.objects.filter(created_at__gte=month_ago).count()
    
    # Recent Activity
    recent_users = User.objects.filter(date_joined__gte=week_ago).order_by('-date_joined')[:5]
    recent_appointments = Appointment.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:5]
    recent_treatments = Treatment.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:5]
    
    # System Health Metrics
    system_health = {
        'database_status': 'healthy',
        'cache_status': 'healthy',
        'storage_usage': '45%',
        'memory_usage': '62%',
        'cpu_usage': '23%',
    }
    
    # Add our dashboard data to the context
    dashboard_context = {
        # User Statistics
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_receptionists': total_receptionists,
        'total_admins': total_admins,
        'new_users_this_month': new_users_this_month,
        'user_growth_percentage': user_growth_percentage,
        'active_users': active_users,
        
        # Appointment Statistics
        'total_appointments': total_appointments,
        'appointments_today': appointments_today,
        'appointments_this_week': appointments_this_week,
        'appointments_this_month': appointments_this_month,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        
        # Treatment Statistics
        'total_treatments': total_treatments,
        'treatments_this_month': treatments_this_month,
        
        # Recent Activity
        'recent_users': recent_users,
        'recent_appointments': recent_appointments,
        'recent_treatments': recent_treatments,
        
        # System Health
        'system_health': system_health,
        
        # Date ranges for display
        'today': today,
        'week_ago': week_ago,
        'month_ago': month_ago,
    }
    
    # Merge with existing context
    context.update(dashboard_context)
    return context