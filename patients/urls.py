from django.urls import path
from django.views.generic import RedirectView

from .views import (
    PatientDashboardView,
    PatientProfileUpdateView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentPrintView,
    ChangePasswordView,
    AddReviewView,
    PrescriptionListView,
    PrescriptionDetailView,
    PrescriptionPrintView,
    MedicalRecordsView,
)
from .api import (
    PatientDashboardAPI,
    PatientAppointmentsAPI,
    PatientPrescriptionsAPI,
    PatientAppointmentCancelAPI,
)

app_name = "patients"

urlpatterns = [
    # Redirect root patients/ URL to patients/dashboard/
    path("", RedirectView.as_view(pattern_name='patients:dashboard'), name="patient-home"),
    
    path("dashboard/", PatientDashboardView.as_view(), name="dashboard"),
    # JSON APIs for React frontend
    path("api/dashboard/", PatientDashboardAPI.as_view(), name="api-dashboard"),
    path("api/appointments/", PatientAppointmentsAPI.as_view(), name="api-appointments"),
    path("api/prescriptions/", PatientPrescriptionsAPI.as_view(), name="api-prescriptions"),
    path("api/appointments/<int:pk>/cancel/", PatientAppointmentCancelAPI.as_view(), name="api-appointment-cancel"),
    path(
        "profile-settings/",
        PatientProfileUpdateView.as_view(),
        name="profile-setting",
    ),
    path(
        "appointments/<int:pk>/",
        AppointmentDetailView.as_view(),
        name="appointment-detail",
    ),
    path(
        "appointments/<int:pk>/cancel/",
        AppointmentCancelView.as_view(),
        name="appointment-cancel",
    ),
    path(
        "appointments/<int:pk>/print/",
        AppointmentPrintView.as_view(),
        name="appointment-print",
    ),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "appointment/<int:booking_id>/review/",
        AddReviewView.as_view(),
        name="add-review",
    ),
    # Prescription URLs
    path(
        "prescriptions/",
        PrescriptionListView.as_view(),
        name="prescriptions",
    ),
    path(
        "prescriptions/<int:pk>/",
        PrescriptionDetailView.as_view(),
        name="prescription-detail",
    ),
    path(
        "prescriptions/<int:pk>/print/",
        PrescriptionPrintView.as_view(),
        name="prescription-print",
    ),
    # Medical Records URL
    path(
        "medical-records/",
        MedicalRecordsView.as_view(),
        name="medical-records",
    ),
]
