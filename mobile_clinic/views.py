from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone

from .models import MobileClinicRequest, MobileClinicNotification
from .forms import MobileClinicRequestForm

@login_required
def request_mobile_clinic(request):
    """View for patients to request a mobile clinic visit"""
    if request.method == 'POST':
        form = MobileClinicRequestForm(request.POST)
        if form.is_valid():
            mobile_request = form.save(commit=False)
            mobile_request.patient = request.user
            mobile_request.save()
            
            # Create notification for admin
            notification = MobileClinicNotification(
                request=mobile_request,
                message=f"New mobile clinic request from {request.user.get_full_name()} for {mobile_request.requested_date}"
            )
            notification.save()
            
            messages.success(request, "Your mobile clinic request has been submitted successfully.")
            return redirect('mobile_clinic:my_requests')
    else:
        form = MobileClinicRequestForm()
    
    return render(request, 'mobile_clinic/request_form.html', {'form': form})

@login_required
def my_requests(request):
    """View for patients to see their mobile clinic requests"""
    requests = MobileClinicRequest.objects.filter(patient=request.user)
    return render(request, 'mobile_clinic/my_requests.html', {'requests': requests})

@login_required
def request_detail(request, pk):
    """View for patients to see details of a specific request"""
    clinic_request = get_object_or_404(MobileClinicRequest, pk=pk, patient=request.user)
    return render(request, 'mobile_clinic/request_detail.html', {'request': clinic_request})

@login_required
def cancel_request(request, pk):
    """View for patients to cancel a request"""
    clinic_request = get_object_or_404(MobileClinicRequest, pk=pk, patient=request.user)
    
    if clinic_request.status in ['pending', 'approved']:
        clinic_request.status = 'cancelled'
        clinic_request.save()
        
        # Create notification for admin
        notification = MobileClinicNotification(
            request=clinic_request,
            message=f"Mobile clinic request cancelled by {request.user.get_full_name()}"
        )
        notification.save()
        
        messages.success(request, "Your mobile clinic request has been cancelled.")
    else:
        messages.error(request, "This request cannot be cancelled.")
    
    return redirect('mobile_clinic:my_requests')

@staff_member_required
def admin_request_list(request):
    """View for admin to see all mobile clinic requests"""
    requests = MobileClinicRequest.objects.all()
    return render(request, 'mobile_clinic/admin_request_list.html', {'requests': requests})

@staff_member_required
def admin_request_detail(request, pk):
    """View for admin to see details of a specific request"""
    clinic_request = get_object_or_404(MobileClinicRequest, pk=pk)
    
    # Mark notifications as read
    notifications = MobileClinicNotification.objects.filter(request=clinic_request, is_read=False)
    for notification in notifications:
        notification.is_read = True
        notification.save()
    
    return render(request, 'mobile_clinic/admin_request_detail.html', {'request': clinic_request})

@staff_member_required
def update_request_status(request, pk):
    """View for admin to update the status of a request"""
    if request.method == 'POST':
        clinic_request = get_object_or_404(MobileClinicRequest, pk=pk)
        status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if status in [s[0] for s in MobileClinicRequest.STATUS_CHOICES]:
            old_status = clinic_request.status
            clinic_request.status = status
            clinic_request.admin_notes = admin_notes
            clinic_request.save()
            
            # Create notification for patient
            notification = MobileClinicNotification(
                request=clinic_request,
                message=f"Your mobile clinic request status has been updated from {old_status} to {status}"
            )
            notification.save()
            
            messages.success(request, f"Request status updated to {status}.")
            return redirect('mobile_clinic:admin_request_detail', pk=pk)
    
    return redirect('mobile_clinic:admin_request_list')

@staff_member_required
def admin_notifications(request):
    """View for admin to see all unread notifications"""
    notifications = MobileClinicNotification.objects.filter(is_read=False)
    return render(request, 'mobile_clinic/admin_notifications.html', {'notifications': notifications})

@staff_member_required
def mark_notification_read(request, pk):
    """View for admin to mark a notification as read"""
    notification = get_object_or_404(MobileClinicNotification, pk=pk)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})