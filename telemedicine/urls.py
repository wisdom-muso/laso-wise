from django.urls import path
from . import views

app_name = 'telemedicine'

urlpatterns = [
    # Main views
    path('', views.TeleMedicineConsultationListView.as_view(), name='list'),
    path('schedule/', views.TeleMedicineConsultationCreateView.as_view(), name='schedule'),
    path('session/<str:meeting_id>/', views.TeleMedicineConsultationDetailView.as_view(), name='detail'),
    path('settings/', views.TeleMedicineSettingsView.as_view(), name='settings'),
    
    # Telemedicine Appointments
    path('appointments/', views.TelemedicineAppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.create_telemedicine_appointment, name='appointment-create'),
    path('appointments/<int:pk>/', views.TelemedicineAppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Video Session Management
    path('session/<int:appointment_id>/start/', views.start_video_session, name='start-session'),
    path('session/<int:session_id>/end/', views.end_video_session, name='end-session'),
]
