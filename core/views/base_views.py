from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.middleware.csrf import get_token
from django.utils import timezone

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
    template_name = "home.html"
    
    def dispatch(self, request, *args, **kwargs):
        # If user is authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            if request.user.role == 'patient':
                from django.shortcuts import redirect
                return redirect('patients:dashboard')
            elif request.user.role == 'doctor':
                from django.shortcuts import redirect
                return redirect('doctors:dashboard')
            elif request.user.is_staff or request.user.is_superuser:
                from django.shortcuts import redirect
                return redirect('admin-dashboard')
        
        # If not authenticated, show the public landing page
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctors = (
            User.objects.select_related("profile")
            .filter(role=USER_ROLE_DOCTOR)
            .filter(is_superuser=False)
        )
        context['doctors'] = doctors
        return context


def csrf_token_view(request):
    """Get CSRF token for frontend"""
    return JsonResponse({
        'csrfToken': get_token(request)
    })