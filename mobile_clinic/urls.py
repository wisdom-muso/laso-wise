from django.urls import path
from . import views

app_name = 'mobile_clinic'

urlpatterns = [
    # Patient URLs
    path('request/', views.request_mobile_clinic, name='request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    
    # Admin URLs
    path('admin/requests/', views.admin_request_list, name='admin_request_list'),
    path('admin/request/<int:pk>/', views.admin_request_detail, name='admin_request_detail'),
    path('admin/request/<int:pk>/update/', views.update_request_status, name='update_request_status'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/notification/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]