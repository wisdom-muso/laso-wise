from django.urls import path

from .views.common_views import *
from .api import MeAPI, MeUpdateAPI, MeDeleteAPI, LoginAPI, RegisterAPI, LogoutAPI

app_name = "accounts"

urlpatterns = [
    path(
        "doctor/register/",
        RegisterDoctorView.as_view(),
        name="doctor-register",
    ),
    path(
        "patient/register/",
        RegisterPatientView.as_view(),
        name="patient-register",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "update-basic-information/",
        UpdateBasicUserInformationAPIView.as_view(),
        name="update-basic-information",
    ),
    # JSON profile APIs
    path("api/me/", MeAPI.as_view(), name="api-me"),
    path("api/me/update/", MeUpdateAPI.as_view(), name="api-me-update"),
    path("api/me/delete/", MeDeleteAPI.as_view(), name="api-me-delete"),
    
    # Authentication APIs
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    path("api/register/", RegisterAPI.as_view(), name="api-register"),
    path("api/logout/", LogoutAPI.as_view(), name="api-logout"),
]
