from django.urls import path
from django.shortcuts import redirect
from .views import home, TermsView, PrivacyView

app_name = "core"

def redirect_to_login(request):
    return redirect('accounts:login')

urlpatterns = [
    path("", redirect_to_login, name="home"),
    path("home/", home, name="home-page"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
]
