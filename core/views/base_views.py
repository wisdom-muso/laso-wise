from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from accounts.models import User
from core.constants import USER_ROLE_DOCTOR


def home(request: HttpRequest) -> HttpResponse:
    doctors = (
        User.objects.select_related("profile")
        .filter(role=USER_ROLE_DOCTOR)
        .filter(is_superuser=False)
    )
    return render(request, "home.html", {"doctors": doctors})


class TermsView(TemplateView):
    template_name = "core/terms.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class IndexView(TemplateView):
    """Redirect to login page as the first page"""
    
    def get(self, request, *args, **kwargs):
        # If user is authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('/dashboard/')
        # If not authenticated, redirect to login
        return redirect('accounts:login')


def csrf_token_view(request):
    """Get CSRF token for frontend"""
    return JsonResponse({
        'csrfToken': get_token(request)
    })