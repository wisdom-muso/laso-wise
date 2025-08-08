from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Max, Min
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

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
        return redirect('core:home')
    
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
                    return redirect('core:home')
            
            # For patients adding their own vitals
            messages.success(request, _("Vital sign recorded successfully."))
            
            # Check if the vital sign is abnormal and create notification
            if vital_record.status in ['critical-low', 'critical-high', 'abnormal-low', 'abnormal-high']:
                severity = 'danger' if 'critical' in vital_record.status else 'warning'
                
                message = _(f"Your {vital_record.category.name} reading of {vital_record.value} {vital_record.category.unit} "
                           f"is {vital_record.status_display.lower()}. Please consult with your doctor.")
                
                VitalNotification.objects.create(
                    patient=vital_record.patient,
                    vital_record=vital_record,
                    message=message,
                    severity=severity
                )
            
            return redirect('vitals:patient-dashboard')
    else:
        form = VitalRecordForm(
            patient=request.user if request.user.role == 'patient' else None,
            recorded_by=request.user
        )
    
    context = {
        'form': form,
    }
    
    return render(request, 'vitals/add_vital_record.html', context)


@login_required
def vital_history(request):
    """
    View for displaying vital sign history
    """
    # Only patients can access this view
    if request.user.role != 'patient':
        messages.error(request, _("Only patients can access this page."))
        return redirect('core:home')
    
    # Get filter form
    form = DateRangeForm(request.GET)
    
    # Apply filters
    vitals = VitalRecord.objects.filter(patient=request.user)
    
    if form.is_valid():
        if form.cleaned_data['start_date']:
            vitals = vitals.filter(recorded_at__date__gte=form.cleaned_data['start_date'])
        
        if form.cleaned_data['end_date']:
            vitals = vitals.filter(recorded_at__date__lte=form.cleaned_data['end_date'])
        
        if form.cleaned_data['category']:
            vitals = vitals.filter(category=form.cleaned_data['category'])
    
    # Order by most recent
    vitals = vitals.select_related('category', 'recorded_by').order_by('-recorded_at')
    
    # Group by category for charts
    chart_data = {}
    categories = VitalCategory.objects.filter(is_active=True)
    
    for category in categories:
        category_records = vitals.filter(category=category)
        
        if category_records.exists():
            dates = [record.recorded_at.strftime('%Y-%m-%d %H:%M') for record in category_records]
            values = [float(record.value) for record in category_records]
            
            chart_data[category.id] = {
                'name': category.name,
                'unit': category.unit,
                'color': category.color,
                'dates': list(reversed(dates)),  # Reverse to show chronological order
                'values': list(reversed(values)),
                'min_normal': category.min_normal,
                'max_normal': category.max_normal,
            }
    
    context = {
        'vitals': vitals,
        'form': form,
        'chart_data': chart_data,
    }
    
    return render(request, 'vitals/vital_history.html', context)


@login_required
def manage_goals(request):
    """
    View for managing vital sign goals
    """
    # Only patients can access this view
    if request.user.role != 'patient':
        messages.error(request, _("Only patients can access this page."))
        return redirect('core:home')
    
    # Get active and achieved goals
    active_goals = VitalGoal.objects.filter(
        patient=request.user,
        is_achieved=False
    ).select_related('category', 'set_by')
    
    achieved_goals = VitalGoal.objects.filter(
        patient=request.user,
        is_achieved=True
    ).select_related('category', 'set_by')
    
    # Form for adding new goal
    if request.method == 'POST':
        form = VitalGoalForm(
            request.POST,
            patient=request.user,
            set_by=request.user
        )
        
        if form.is_valid():
            form.save()
            messages.success(request, _("Goal added successfully."))
            return redirect('vitals:manage-goals')
    else:
        form = VitalGoalForm(
            patient=request.user,
            set_by=request.user
        )
    
    context = {
        'active_goals': active_goals,
        'achieved_goals': achieved_goals,
        'form': form,
    }
    
    return render(request, 'vitals/manage_goals.html', context)


@login_required
@require_POST
def mark_goal_achieved(request, goal_id):
    """
    Mark a goal as achieved
    """
    goal = get_object_or_404(VitalGoal, id=goal_id, patient=request.user)
    goal.is_achieved = True
    goal.achieved_date = timezone.now().date()
    goal.save()
    
    messages.success(request, _("Goal marked as achieved!"))
    return redirect('vitals:manage-goals')


@login_required
@require_POST
def delete_goal(request, goal_id):
    """
    Delete a goal
    """
    goal = get_object_or_404(VitalGoal, id=goal_id, patient=request.user)
    goal.delete()
    
    messages.success(request, _("Goal deleted successfully."))
    return redirect('vitals:manage-goals')


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read
    """
    notification = get_object_or_404(VitalNotification, id=notification_id, patient=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('vitals:patient-dashboard')


# Doctor and Admin Views

@login_required
def patient_vitals(request, patient_id):
    """
    View for doctors and admins to see a patient's vital signs
    """
    # Only doctors and admins can access this view
    if request.user.role not in ['doctor', 'admin']:
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('core:home')
    
    # Get the patient
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
    
    # Get all vital records for this patient
    vitals = VitalRecord.objects.filter(
        patient=patient
    ).select_related('category', 'recorded_by').order_by('-recorded_at')
    
    # Get active goals
    active_goals = VitalGoal.objects.filter(
        patient=patient,
        is_achieved=False
    ).select_related('category', 'set_by')
    
    # Form for adding new vital record
    form = VitalRecordForm(patient=patient, recorded_by=request.user)
    
    # Form for adding new goal
    goal_form = VitalGoalForm(patient=patient, set_by=request.user)
    
    context = {
        'patient': patient,
        'latest_vitals': latest_vitals,
        'categories': categories,
        'vitals': vitals,
        'active_goals': active_goals,
        'form': form,
        'goal_form': goal_form,
    }
    
    return render(request, 'vitals/patient_vitals.html', context)


@login_required
def add_patient_vital(request, patient_id):
    """
    View for doctors and admins to add a vital record for a patient
    """
    # Only doctors and admins can access this view
    if request.user.role not in ['doctor', 'admin']:
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('core:home')
    
    # Get the patient
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    if request.method == 'POST':
        form = VitalRecordForm(request.POST, patient=patient, recorded_by=request.user)
        
        if form.is_valid():
            vital_record = form.save()
            
            messages.success(request, _(f"Vital sign recorded for {patient.get_full_name()}."))
            
            # Check if the vital sign is abnormal and create notification
            if vital_record.status in ['critical-low', 'critical-high', 'abnormal-low', 'abnormal-high']:
                severity = 'danger' if 'critical' in vital_record.status else 'warning'
                
                message = _(f"Your {vital_record.category.name} reading of {vital_record.value} {vital_record.category.unit} "
                           f"is {vital_record.status_display.lower()}. Please consult with your doctor.")
                
                VitalNotification.objects.create(
                    patient=vital_record.patient,
                    vital_record=vital_record,
                    message=message,
                    severity=severity
                )
            
            # Redirect to patient vitals page
            return redirect('vitals:patient-vitals', patient_id=patient.id)
    else:
        form = VitalRecordForm(patient=patient, recorded_by=request.user)
    
    context = {
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'vitals/add_patient_vital.html', context)


@login_required
def add_patient_goal(request, patient_id):
    """
    View for doctors and admins to add a goal for a patient
    """
    # Only doctors and admins can access this view
    if request.user.role not in ['doctor', 'admin']:
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('core:home')
    
    # Get the patient
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    if request.method == 'POST':
        form = VitalGoalForm(request.POST, patient=patient, set_by=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, _(f"Goal added for {patient.get_full_name()}."))
            return redirect('vitals:patient-vitals', patient_id=patient.id)
    else:
        form = VitalGoalForm(patient=patient, set_by=request.user)
    
    context = {
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'vitals/add_patient_goal.html', context)


# API Views for Charts

@login_required
def vital_chart_data(request, category_id):
    """
    API view for getting chart data for a specific vital category
    """
    # Only patients, doctors, and admins can access this view
    if request.user.role not in ['patient', 'doctor', 'admin']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get the category
    category = get_object_or_404(VitalCategory, id=category_id, is_active=True)
    
    # Get the patient
    patient_id = request.GET.get('patient_id')
    if patient_id and request.user.role in ['doctor', 'admin']:
        patient = get_object_or_404(User, id=patient_id, role='patient')
    else:
        patient = request.user
    
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=days)
    
    # Get records
    records = VitalRecord.objects.filter(
        patient=patient,
        category=category,
        recorded_at__gte=start_date,
        recorded_at__lte=end_date
    ).order_by('recorded_at')
    
    # Prepare data
    dates = [record.recorded_at.strftime('%Y-%m-%d %H:%M') for record in records]
    values = [float(record.value) for record in records]
    
    # Get statistics
    stats = {}
    if records.exists():
        stats = {
            'avg': records.aggregate(avg=Avg('value'))['avg'],
            'min': records.aggregate(min=Min('value'))['min'],
            'max': records.aggregate(max=Max('value'))['max'],
            'count': records.count(),
            'first_date': records.first().recorded_at.strftime('%Y-%m-%d'),
            'last_date': records.last().recorded_at.strftime('%Y-%m-%d'),
        }
    
    data = {
        'category': {
            'id': category.id,
            'name': category.name,
            'unit': category.unit,
            'color': category.color,
            'min_normal': category.min_normal,
            'max_normal': category.max_normal,
        },
        'dates': dates,
        'values': values,
        'stats': stats,
    }
    
    return JsonResponse(data)