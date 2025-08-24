from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.generic import View
from .forms import LoginForm


class CustomLoginView(DjangoLoginView):
    """
    Custom login view that properly handles redirects after successful login
    """
    template_name = 'core/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """
        Return the URL to redirect to after processing a valid form.
        """
        # First check if there's a 'next' parameter
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        if next_url:
            # Ensure the URL is safe to redirect to
            from django.utils.http import url_has_allowed_host_and_scheme
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
                return next_url
        
        # Fallback to LOGIN_REDIRECT_URL
        return getattr(settings, 'LOGIN_REDIRECT_URL', reverse_lazy('dashboard'))
    
    def form_valid(self, form):
        """
        Security check complete. Log the user in and redirect to success URL.
        """
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, _('Welcome back! You have been successfully logged in.'))
        
        return response
    
    def form_invalid(self, form):
        """
        If the form is invalid, add error message and render the form again.
        """
        messages.error(self.request, _('Login failed. Please check your username and password.'))
        return super().form_invalid(form)


class HomeRedirectView(View):
    """
    Custom view for the root URL that redirects authenticated users to dashboard
    and unauthenticated users to login page
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return redirect('login')