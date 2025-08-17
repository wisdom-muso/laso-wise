from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Max, Min, Count, Q
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta, datetime
import json

from .models import VitalRecord, VitalCategory, VitalGoal, VitalNotification
from .forms import VitalRecordForm, VitalGoalForm, DateRangeForm

User = get_user_model()


@login_required
def patient_vitals_dashboard(request):
    """
    Dashboard view for patients to see their vital signs
    """
    # Only patients can access this view
    if request.user.role != 'patient':
        messages.error(request, _("Only patients can access this page."))
        return redirect('core:index')
    
    # Get latest vital records for each category
    categories = VitalCategory.objects.filter(is_active=True)
    latest_vitals = {}
    
    for category in categories:
        latest = VitalRecord.objects.filter(
            patient=request.user,
            category=category
        ).order_by('-recorded_at').first()
        
        if latest:
            latest_vitals[category.id] = latest
    
    # Get active goals
    active_goals = VitalGoal.objects.filter(
        patient=request.user,
        is_achieved=False
    ).select_related('category')
    
    # Get unread notifications
    notifications = VitalNotification.objects.filter(
        patient=request.user,
        is_read=False
    ).select_related('vital_record', 'vital_record__category')
    
    # Form for adding new vital record
    form = VitalRecordForm(patient=request.user, recorded_by=request.user)
    
    context = {
        'latest_vitals': latest_vitals,
        'categories': categories,
        'active_goals': active_goals,
        'notifications': notifications,
        'form': form,
    }
    
    return render(request, 'vitals/patient_dashboard.html', context)


@login_required
def add_vital_record(request):
    """
    View for adding a new vital record
    """
    if request.method == 'POST':
        form = VitalRecordForm(
            request.POST,
            patient=request.user if request.user.role == 'patient' else None,
            recorded_by=request.user
        )
        
        if form.is_valid():
            vital_record = form.save()
            
            # If this is a doctor or admin adding a record for a patient
            if request.user.role in ['doctor', 'admin'] and 'patient_id' in request.POST:
                try:
                    patient = User.objects.get(id=request.POST.get('patient_id'), role='patient')
                    vital_record.patient = patient
                    vital_record.is_professional_reading = True
                    vital_record.save()
                    
                    messages.success(request, _(f"Vital sign recorded for {patient.get_full_name()}."))
                    
                    # Redirect to patient detail page if doctor/admin
                    if request.user.role == 'doctor':
                        return redirect('doctors:patient-detail', patient.id)
                    return redirect('admin-patients')
                except User.DoesNotExist:
                    messages.error(request, _("Patient not found."))
                    return redirect('core:index')
            
            # For patients adding their own vitals
            messages.success(request, _("Vital sign recorded successfully."))
            return redirect('vitals:patient-dashboard')
    else:
        form = VitalRecordForm(
            patient=request.user if request.user.role == 'patient' else None,
            recorded_by=request.user
        )
    
    context = {
        'form': form,
        'categories': VitalCategory.objects.filter(is_active=True)
    }
    
    return render(request, 'vitals/add_vital_record.html', context)


@login_required
def vital_history(request):
    """
    View for displaying vital sign history with charts
    """
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get vital records for the date range
    vital_records = VitalRecord.objects.filter(
        patient=request.user if request.user.role == 'patient' else None,
        recorded_at__date__range=[start_date, end_date]
    ).select_related('category').order_by('-recorded_at')
    
    # Get categories for filtering
    categories = VitalCategory.objects.filter(is_active=True)
    selected_category = request.GET.get('category')
    
    if selected_category:
        vital_records = vital_records.filter(category_id=selected_category)
    
    # Prepare chart data
    chart_data = prepare_chart_data(vital_records, start_date, end_date)
    
    # Date range form
    date_form = DateRangeForm(initial={
        'start_date': start_date,
        'end_date': end_date,
        'category': selected_category
    })
    
    context = {
        'vital_records': vital_records,
        'categories': categories,
        'selected_category': selected_category,
        'chart_data': chart_data,
        'date_form': date_form,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'vitals/vital_history.html', context)


def prepare_chart_data(vital_records, start_date, end_date):
    """
    Prepare chart data for vital signs visualization
    """
    chart_data = {
        'labels': [],
        'datasets': []
    }
    
    # Generate date labels
    current_date = start_date
    while current_date <= end_date:
        chart_data['labels'].append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Get unique categories from the records
    categories = vital_records.values_list('category__name', 'category__color').distinct()
    
    for category_name, category_color in categories:
        dataset = {
            'label': category_name,
            'data': [],
            'borderColor': category_color or '#14b8a6',
            'backgroundColor': category_color + '20' if category_color else '#14b8a620',
            'borderWidth': 2,
            'fill': False,
            'tension': 0.4
        }
        
        # Fill data for each date
        current_date = start_date
        while current_date <= end_date:
            daily_avg = vital_records.filter(
                category__name=category_name,
                recorded_at__date=current_date
            ).aggregate(avg_value=Avg('value'))['avg_value']
            
            dataset['data'].append(daily_avg if daily_avg else None)
            current_date += timedelta(days=1)
        
        chart_data['datasets'].append(dataset)
    
    return chart_data


@login_required
def manage_goals(request):
    """
    View for managing health goals
    """
    if request.method == 'POST':
        form = VitalGoalForm(
            request.POST,
            patient=request.user if request.user.role == 'patient' else None,
            set_by=request.user
        )
        
        if form.is_valid():
            goal = form.save()
            messages.success(request, _("Health goal set successfully."))
            return redirect('vitals:manage-goals')
    else:
        form = VitalGoalForm(
            patient=request.user if request.user.role == 'patient' else None,
            set_by=request.user
        )
    
    # Get all goals (active and achieved)
    goals = VitalGoal.objects.filter(
        patient=request.user if request.user.role == 'patient' else None
    ).select_related('category').order_by('-created_at')
    
    context = {
        'form': form,
        'goals': goals,
        'categories': VitalCategory.objects.filter(is_active=True)
    }
    
    return render(request, 'vitals/manage_goals.html', context)


@login_required
@require_POST
def mark_goal_achieved(request, goal_id):
    """
    Mark a health goal as achieved
    """
    try:
        goal = VitalGoal.objects.get(
            id=goal_id,
            patient=request.user if request.user.role == 'patient' else None
        )
        goal.is_achieved = True
        goal.achieved_date = timezone.now().date()
        goal.save()
        messages.success(request, _("Goal marked as achieved!"))
    except VitalGoal.DoesNotExist:
        messages.error(request, _("Goal not found."))
    
    return redirect('vitals:manage-goals')


@login_required
@require_POST
def delete_goal(request, goal_id):
    """
    Delete a health goal
    """
    try:
        goal = VitalGoal.objects.get(
            id=goal_id,
            patient=request.user if request.user.role == 'patient' else None
        )
        goal.delete()
        messages.success(request, _("Goal deleted successfully."))
    except VitalGoal.DoesNotExist:
        messages.error(request, _("Goal not found."))
    
    return redirect('vitals:manage-goals')


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read
    """
    try:
        notification = VitalNotification.objects.get(
            id=notification_id,
            patient=request.user if request.user.role == 'patient' else None
        )
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return JsonResponse({'status': 'success'})
    except VitalNotification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)


@login_required
def patient_vitals(request, patient_id):
    """
    View for doctors/admins to see patient vitals
    """
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    # Get latest vital records for each category
    categories = VitalCategory.objects.filter(is_active=True)
    latest_vitals = {}
    
    for category in categories:
        latest = VitalRecord.objects.filter(
            patient=patient,
            category=category
        ).order_by('-recorded_at').first()
        
        if latest:
            latest_vitals[category.id] = latest
    
    # Get active goals
    active_goals = VitalGoal.objects.filter(
        patient=patient,
        is_achieved=False
    ).select_related('category')
    
    # Get unread notifications
    notifications = VitalNotification.objects.filter(
        patient=patient,
        is_read=False
    ).select_related('vital_record', 'vital_record__category')
    
    # Calculate statistics
    total_vitals = VitalRecord.objects.filter(patient=patient).count()
    normal_vitals = VitalRecord.objects.filter(patient=patient, status='normal').count()
    abnormal_vitals = VitalRecord.objects.filter(
        patient=patient, 
        status__in=['abnormal-low', 'abnormal-high']
    ).count()
    critical_vitals = VitalRecord.objects.filter(
        patient=patient, 
        status__in=['critical-low', 'critical-high']
    ).count()
    
    # Prepare chart data for the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    vital_records = VitalRecord.objects.filter(
        patient=patient,
        recorded_at__date__range=[start_date, end_date]
    ).select_related('category').order_by('recorded_at')
    
    chart_data = prepare_chart_data(vital_records, start_date, end_date)
    
    # Prepare chart labels and datasets for template
    chart_labels = json.dumps(chart_data['labels'])
    chart_datasets = json.dumps(chart_data['datasets'])
    
    context = {
        'patient': patient,
        'latest_vitals': latest_vitals,
        'categories': categories,
        'active_goals': active_goals,
        'notifications': notifications,
        'total_vitals': total_vitals,
        'normal_vitals': normal_vitals,
        'abnormal_vitals': abnormal_vitals,
        'critical_vitals': critical_vitals,
        'chart_labels': chart_labels,
        'chart_datasets': chart_datasets,
    }
    
    return render(request, 'vitals/patient_vitals.html', context)


@login_required
def add_patient_vital(request, patient_id):
    """
    View for doctors/admins to add vitals for a patient
    """
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    if request.method == 'POST':
        form = VitalRecordForm(
            request.POST,
            patient=patient,
            recorded_by=request.user
        )
        
        if form.is_valid():
            vital_record = form.save()
            vital_record.is_professional_reading = True
            vital_record.save()
            
            messages.success(request, _(f"Vital sign recorded for {patient.get_full_name()}."))
            
            # Redirect based on user role
            if request.user.role == 'doctor':
                return redirect('doctors:patient-detail', patient.id)
            return redirect('admin-patients')
    else:
        form = VitalRecordForm(
            patient=patient,
            recorded_by=request.user
        )
    
    context = {
        'form': form,
        'patient': patient,
        'categories': VitalCategory.objects.filter(is_active=True)
    }
    
    return render(request, 'vitals/add_patient_vital.html', context)


@login_required
def add_patient_goal(request, patient_id):
    """
    View for doctors/admins to add goals for a patient
    """
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    if request.method == 'POST':
        form = VitalGoalForm(
            request.POST,
            patient=patient,
            set_by=request.user
        )
        
        if form.is_valid():
            goal = form.save()
            messages.success(request, _(f"Health goal set for {patient.get_full_name()}."))
            
            # Redirect based on user role
            if request.user.role == 'doctor':
                return redirect('doctors:patient-detail', patient.id)
            return redirect('admin-patients')
    else:
        form = VitalGoalForm(
            patient=patient,
            set_by=request.user
        )
    
    context = {
        'form': form,
        'patient': patient,
        'categories': VitalCategory.objects.filter(is_active=True)
    }
    
    return render(request, 'vitals/add_patient_goal.html', context)


@login_required
def vital_chart_data(request, category_id):
    """
    API endpoint for getting vital chart data (for real-time updates)
    """
    patient_id = request.GET.get('patient_id')
    if not patient_id:
        return JsonResponse({'error': 'Patient ID required'}, status=400)
    
    try:
        patient = User.objects.get(id=patient_id, role='patient')
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    
    # Get vital records for the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    vital_records = VitalRecord.objects.filter(
        patient=patient,
        recorded_at__date__range=[start_date, end_date]
    ).select_related('category')
    
    if category_id and category_id != '0':
        vital_records = vital_records.filter(category_id=category_id)
    
    # Calculate statistics
    stats = {
        'total': vital_records.count(),
        'normal': vital_records.filter(status='normal').count(),
        'abnormal': vital_records.filter(status__in=['abnormal-low', 'abnormal-high']).count(),
        'critical': vital_records.filter(status__in=['critical-low', 'critical-high']).count(),
    }
    
    # Prepare chart data
    chart_data = prepare_chart_data(vital_records, start_date, end_date)
    
    return JsonResponse({
        'stats': stats,
        'chart_data': chart_data,
        'last_updated': timezone.now().isoformat()
    })


@login_required
def vitals_analytics(request, patient_id=None):
    """
    Advanced analytics view for vitals data
    """
    if patient_id:
        patient = get_object_or_404(User, id=patient_id, role='patient')
        vital_records = VitalRecord.objects.filter(patient=patient)
    else:
        patient = request.user if request.user.role == 'patient' else None
        vital_records = VitalRecord.objects.filter(patient=request.user)
    
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # Last 90 days for better analytics
    
    vital_records = vital_records.filter(
        recorded_at__date__range=[start_date, end_date]
    ).select_related('category')
    
    # Advanced analytics
    analytics = {
        'trends': calculate_trends(vital_records),
        'patterns': analyze_patterns(vital_records),
        'risks': assess_risks(vital_records),
        'recommendations': generate_recommendations(vital_records),
        'summary': generate_summary(vital_records)
    }
    
    context = {
        'patient': patient,
        'analytics': analytics,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'vitals/vitals_analytics.html', context)


def calculate_trends(vital_records):
    """
    Calculate trends in vital signs
    """
    trends = {}
    
    for category in VitalCategory.objects.filter(is_active=True):
        category_records = vital_records.filter(category=category)
        
        if category_records.exists():
            # Calculate trend over time
            daily_avgs = category_records.annotate(
                date=TruncDate('recorded_at')
            ).values('date').annotate(
                avg_value=Avg('value')
            ).order_by('date')
            
            if len(daily_avgs) > 1:
                first_avg = daily_avgs.first()['avg_value']
                last_avg = daily_avgs.last()['avg_value']
                change = ((last_avg - first_avg) / first_avg) * 100
                
                trends[category.name] = {
                    'change_percent': round(change, 2),
                    'trend': 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable',
                    'first_value': round(first_avg, 2),
                    'last_value': round(last_avg, 2)
                }
    
    return trends


def analyze_patterns(vital_records):
    """
    Analyze patterns in vital signs
    """
    patterns = {}
    
    for category in VitalCategory.objects.filter(is_active=True):
        category_records = vital_records.filter(category=category)
        
        if category_records.exists():
            # Time-based patterns
            hourly_patterns = category_records.annotate(
                hour=TruncHour('recorded_at')
            ).values('hour__hour').annotate(
                avg_value=Avg('value'),
                count=Count('id')
            ).order_by('hour__hour')
            
            # Status distribution
            status_distribution = category_records.values('status').annotate(
                count=Count('id')
            )
            
            patterns[category.name] = {
                'hourly_patterns': list(hourly_patterns),
                'status_distribution': list(status_distribution),
                'total_readings': category_records.count(),
                'avg_value': category_records.aggregate(avg=Avg('value'))['avg']
            }
    
    return patterns


def assess_risks(vital_records):
    """
    Assess health risks based on vital signs
    """
    risks = []
    
    # Check for critical readings
    critical_readings = vital_records.filter(
        status__in=['critical-low', 'critical-high']
    ).select_related('category')
    
    for record in critical_readings:
        risks.append({
            'type': 'critical',
            'category': record.category.name,
            'value': record.value,
            'status': record.status,
            'date': record.recorded_at,
            'message': f"Critical {record.category.name} reading: {record.value} {record.category.unit}"
        })
    
    # Check for abnormal trends
    for category in VitalCategory.objects.filter(is_active=True):
        category_records = vital_records.filter(category=category)
        
        if category_records.count() >= 5:  # Need at least 5 readings for trend analysis
            recent_records = category_records.order_by('-recorded_at')[:5]
            recent_avg = sum(r.value for r in recent_records) / len(recent_records)
            
            if category.min_normal and recent_avg < category.min_normal:
                risks.append({
                    'type': 'trend',
                    'category': category.name,
                    'value': recent_avg,
                    'status': 'below_normal',
                    'message': f"{category.name} trending below normal range"
                })
            elif category.max_normal and recent_avg > category.max_normal:
                risks.append({
                    'type': 'trend',
                    'category': category.name,
                    'value': recent_avg,
                    'status': 'above_normal',
                    'message': f"{category.name} trending above normal range"
                })
    
    return risks


def generate_recommendations(vital_records):
    """
    Generate health recommendations based on vital signs
    """
    recommendations = []
    
    # Check for missing vital signs
    categories = VitalCategory.objects.filter(is_active=True)
    for category in categories:
        category_records = vital_records.filter(category=category)
        
        if not category_records.exists():
            recommendations.append({
                'type': 'missing_data',
                'category': category.name,
                'message': f"Consider recording {category.name} readings for better health monitoring"
            })
    
    # Check for abnormal patterns
    for category in categories:
        category_records = vital_records.filter(category=category)
        
        if category_records.count() >= 3:
            abnormal_count = category_records.filter(
                status__in=['abnormal-low', 'abnormal-high', 'critical-low', 'critical-high']
            ).count()
            
            if abnormal_count > category_records.count() * 0.5:  # More than 50% abnormal
                recommendations.append({
                    'type': 'abnormal_pattern',
                    'category': category.name,
                    'message': f"Consider consulting a healthcare provider about {category.name} readings"
                })
    
    return recommendations


def generate_summary(vital_records):
    """
    Generate a summary of vital signs data
    """
    if not vital_records.exists():
        return {
            'total_readings': 0,
            'categories_covered': 0,
            'health_score': 0,
            'last_reading': None
        }
    
    total_readings = vital_records.count()
    categories_covered = vital_records.values('category').distinct().count()
    
    # Calculate health score based on normal readings
    normal_readings = vital_records.filter(status='normal').count()
    health_score = (normal_readings / total_readings) * 100 if total_readings > 0 else 0
    
    last_reading = vital_records.order_by('-recorded_at').first()
    
    return {
        'total_readings': total_readings,
        'categories_covered': categories_covered,
        'health_score': round(health_score, 1),
        'last_reading': last_reading.recorded_at if last_reading else None,
        'normal_percentage': round((normal_readings / total_readings) * 100, 1) if total_readings > 0 else 0
    }