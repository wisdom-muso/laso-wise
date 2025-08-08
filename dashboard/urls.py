from django.urls import path
from .views.bulk_operations import (
    BulkDoctorImportView, BulkDoctorExportView, 
    BulkDoctorUpdateView, BulkDoctorTemplateView
)
from .views.analytics import (
    HospitalAnalyticsView, DoctorAnalyticsView, PatientAnalyticsView
)

urlpatterns = [
    # Bulk Operations
    path('doctors/bulk-import/', BulkDoctorImportView.as_view(), name='bulk-doctor-import'),
    path('doctors/bulk-export/', BulkDoctorExportView.as_view(), name='bulk-doctor-export'),
    path('doctors/bulk-update/', BulkDoctorUpdateView.as_view(), name='bulk-doctor-update'),
    path('doctors/import-template/', BulkDoctorTemplateView.as_view(), name='bulk-doctor-template'),
    
    # Analytics
    path('analytics/hospital/', HospitalAnalyticsView.as_view(), name='hospital-analytics'),
    path('analytics/doctor/<int:doctor_id>/', DoctorAnalyticsView.as_view(), name='doctor-analytics'),
    path('analytics/patient/<int:patient_id>/', PatientAnalyticsView.as_view(), name='patient-analytics'),
]