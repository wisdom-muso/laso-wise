from django.urls import path
from . import views

app_name = 'vitals'

urlpatterns = [
    # Patient views
    path('dashboard/', views.patient_vitals_dashboard, name='patient-dashboard'),
    path('add/', views.add_vital_record, name='add-vital'),
    path('history/', views.vital_history, name='vital-history'),
    path('goals/', views.manage_goals, name='manage-goals'),
    path('goals/<int:goal_id>/achieve/', views.mark_goal_achieved, name='mark-goal-achieved'),
    path('goals/<int:goal_id>/delete/', views.delete_goal, name='delete-goal'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('analytics/', views.vitals_analytics, name='vitals-analytics'),
    
    # Doctor and Admin views
    path('patients/<int:patient_id>/', views.patient_vitals, name='patient-vitals'),
    path('patients/<int:patient_id>/add/', views.add_patient_vital, name='add-patient-vital'),
    path('patients/<int:patient_id>/goals/add/', views.add_patient_goal, name='add-patient-goal'),
    path('patients/<int:patient_id>/analytics/', views.vitals_analytics, name='patient-vitals-analytics'),
    
    # API views
    path('api/chart/<int:category_id>/', views.vital_chart_data, name='vital-chart-data'),
]