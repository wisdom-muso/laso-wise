from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q

from .models_communication import CommunicationNotification

class NotificationListView(LoginRequiredMixin, ListView):
    """
    View to list all notifications for the user.
    """
    model = CommunicationNotification
    template_name = 'core/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 15
    
    def get_queryset(self):
        # Only show notifications for the logged-in user
        return CommunicationNotification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional required data
        context['unread_count'] = CommunicationNotification.objects.filter(
            user=self.request.user,
            is_read=False
        ).count()
        return context

@login_required
def mark_notification_as_read(request, notification_id):
    """
    View to mark a specific notification as read.
    """
    notification = get_object_or_404(CommunicationNotification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # JSON response for AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Redirect for normal request
    messages.success(request, _('Notification marked as read.'))
    if notification.related_url:
        return redirect(notification.related_url)
    return redirect('core:notification-list')

@login_required
def mark_all_notifications_as_read(request):
    """
    View to mark all notifications as read for the user.
    """
    CommunicationNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # AJAX isteği için JSON yanıtı
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Normal istek için yönlendirme
    messages.success(request, _('All notifications marked as read.'))
    return redirect('core:notification-list')
