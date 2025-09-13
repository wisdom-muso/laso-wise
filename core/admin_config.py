from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.http import HttpResponseRedirect


class CustomAdminSite(AdminSite):
    """
    Custom admin site that handles login redirects properly
    """
    site_header = 'LASO Healthcare Administration'
    site_title = 'LASO Admin'
    index_title = 'Welcome to LASO Healthcare Administration'
    
    def login(self, request, extra_context=None):
        """
        Override login to redirect to our custom admin login view
        """
        if request.method == 'GET':
            # Redirect to our custom admin login view
            next_url = request.GET.get('next', '/admin/')
            return HttpResponseRedirect(f'/admin/login/?next={next_url}')
        
        # For POST requests, use the default behavior
        return super().login(request, extra_context)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')