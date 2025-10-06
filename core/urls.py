from django.urls import path
from django.views.generic import RedirectView
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
    export_analytics, enhanced_vitals_dashboard
)
from .views_ai_dashboard import (
    AIRiskAssessmentView, AIRiskAssessmentResultsView, DoctorAIDashboardView,
    SuperAdminAIDashboardView, run_ai_analysis, ai_dashboard_api, generate_risk_report
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
    
    # Enhanced Vitals Dashboard
    path('vitals/enhanced/', enhanced_vitals_dashboard, name='enhanced-vitals'),
    
    # Alternative dashboard endpoint for API access
    path('api/dashboard/', RedirectView.as_view(pattern_name='dashboard', permanent=True), name='api-dashboard'),

    # Patients
    path('patients/register/', views.PatientRegistrationView.as_view(), name='patient-register'),
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    
    # Doctors
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/create/', views.DoctorCreationView.as_view(), name='doctor-create'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<int:pk>/update/', views.DoctorUpdateView.as_view(), name='doctor-update'),
    
    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:pk>/update/', views.AppointmentUpdateView.as_view(), name='appointment-update'),
    path('appointments/<int:pk>/delete/', views.AppointmentDeleteView.as_view(), name='appointment-delete'),
    
    # Treatments
    path('appointments/<int:appointment_id>/treatment/create/', views.TreatmentCreateView.as_view(), name='treatment-create'),
    path('treatments/<int:pk>/', views.TreatmentDetailView.as_view(), name='treatment-detail'),
    path('treatments/<int:pk>/update/', views.TreatmentUpdateView.as_view(), name='treatment-update'),
    
    # Medical History
    path('patients/<int:patient_id>/medical-history/', MedicalHistoryListView.as_view(), name='medical-history-list'),
    path('patients/<int:patient_id>/medical-history/create/', MedicalHistoryCreateView.as_view(), name='medical-history-create'),
    path('medical-history/<int:pk>/update/', MedicalHistoryUpdateView.as_view(), name='medical-history-update'),
    path('medical-history/<int:pk>/delete/', MedicalHistoryDeleteView.as_view(), name='medical-history-delete'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_as_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_as_read, name='mark-all-notifications-read'),
    
    # Theme Settings
    path('theme/toggle/', toggle_theme, name='toggle-theme'),
    path('theme/preference/', get_theme_preference, name='get-theme-preference'),
    
    # Analytics Dashboard
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    
    # Profile Settings
    path('profile/settings/', views.ProfileSettingsView.as_view(), name='profile-settings'),
    
    # Admin Login Sessions
    path('admin/login-sessions/', views.LoginSessionListView.as_view(), name='login-sessions'),
    
    # AI Dashboard URLs
    path('ai/dashboard/doctor/', DoctorAIDashboardView.as_view(), name='doctor-ai-dashboard'),
    path('ai/dashboard/admin/', SuperAdminAIDashboardView.as_view(), name='superadmin-ai-dashboard'),
    path('ai/assessment/<int:patient_id>/', AIRiskAssessmentView.as_view(), name='ai-risk-assessment'),
    path('ai/assessment/<int:patient_id>/results/', AIRiskAssessmentResultsView.as_view(), name='ai-risk-assessment-results'),
    path('ai/assessment/<int:patient_id>/run/', run_ai_analysis, name='run-ai-analysis'),
    path('ai/dashboard/api/<int:patient_id>/', ai_dashboard_api, name='ai-dashboard-api'),
    path('ai/report/<int:patient_id>/', generate_risk_report, name='generate-risk-report'),
]