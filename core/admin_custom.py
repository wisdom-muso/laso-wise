from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import HttpResponseRedirect


class CustomAdminLoginView(LoginView):
    """
    Custom admin login view that redirects to admin dashboard after login
    """
    template_name = 'admin/login.html'
    
    def get_success_url(self):
        """
        Redirect to admin dashboard after successful admin login
        """
        # Check if there's a 'next' parameter for admin
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        if next_url and next_url.startswith('/admin/'):
            return next_url
            
        # Default to admin index for admin users
        return '/admin/'
    
    def form_valid(self, form):
        """
        Security check complete. Log the user in and redirect to admin.
        """
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())


class CustomAdminSite(AdminSite):
    """
    Custom admin site with proper login redirect
    """
    site_title = "LASO Healthcare Admin"
    site_header = "LASO Healthcare Administration"
    index_title = "Welcome to LASO Healthcare Admin"
    
    def login(self, request, extra_context=None):
        """
        Display the login form for the given HttpRequest.
        """
        if request.method == 'GET' and self.has_permission(request):
            # Already logged-in, redirect to admin index
            index_path = reverse('admin:index', current_app=self.name)
            return HttpResponseRedirect(index_path)
            
        # Use custom login view
        login_view = CustomAdminLoginView.as_view(
            template_name=self.login_template or 'admin/login.html',
            extra_context={
                **(extra_context or {}),
                'title': 'Log in',
                'app_path': request.get_full_path(),
                'username': request.user.get_username(),
            }
        )
        return login_view(request)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')