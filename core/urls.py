from django.urls import path
from . import views
from .views_medical_history import (
    MedicalHistoryListView, MedicalHistoryCreateView, 
    MedicalHistoryUpdateView, MedicalHistoryDeleteView
)
from .views_notification import (
    NotificationListView, mark_notification_as_read, mark_all_notifications_as_read
)
from .views_theme import toggle_theme, get_theme_preference
from .views_dashboard import (
    EnhancedDashboardView, DoctorPerformanceView, SystemReportsView,
    dashboard_analytics_api, patient_health_summary_api, recent_activity,
    export_analytics
)

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('dashboard/', EnhancedDashboardView.as_view(), name='enhanced-dashboard'),
    path('dashboard/doctor-performance/', DoctorPerformanceView.as_view(), name='doctor-performance'),
    path('dashboard/system-reports/', SystemReportsView.as_view(), name='system-reports'),
    
    # Dashboard API endpoints
    path('dashboard/api/analytics/', dashboard_analytics_api, name='dashboard-analytics-api'),
    path('dashboard/api/patient/<int:patient_id>/health-summary/', patient_health_summary_api, name='patient-health-summary-api'),
    path('dashboard/api/recent-activity/', recent_activity, name='recent_activity'),
    path('dashboard/api/export-analytics/', export_analytics, name='export_analytics'),

    # Hastalar
    path('patients/register/', views.PatientRegistrationView.as_view(), name='patient-register'),
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    
    # Doktorlar
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/create/', views.DoctorCreationView.as_view(), name='doctor-create'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<int:pk>/update/', views.DoctorUpdateView.as_view(), name='doctor-update'),
    
    # Randevular
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:pk>/update/', views.AppointmentUpdateView.as_view(), name='appointment-update'),
    path('appointments/<int:pk>/delete/', views.AppointmentDeleteView.as_view(), name='appointment-delete'),
    
    # Tedaviler
    path('appointments/<int:appointment_id>/treatment/create/', views.TreatmentCreateView.as_view(), name='treatment-create'),
    path('treatments/<int:pk>/', views.TreatmentDetailView.as_view(), name='treatment-detail'),
    path('treatments/<int:pk>/update/', views.TreatmentUpdateView.as_view(), name='treatment-update'),
    
    # Sağlık Geçmişi
    path('patients/<int:patient_id>/medical-history/', MedicalHistoryListView.as_view(), name='medical-history-list'),
    path('patients/<int:patient_id>/medical-history/create/', MedicalHistoryCreateView.as_view(), name='medical-history-create'),
    path('medical-history/<int:pk>/update/', MedicalHistoryUpdateView.as_view(), name='medical-history-update'),
    path('medical-history/<int:pk>/delete/', MedicalHistoryDeleteView.as_view(), name='medical-history-delete'),
    
    # Bildirimler
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_as_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_as_read, name='mark-all-notifications-read'),
    
    # Tema Ayarları
    path('theme/toggle/', toggle_theme, name='toggle-theme'),
    path('theme/preference/', get_theme_preference, name='get-theme-preference'),
    
    # Analytics Dashboard
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
]