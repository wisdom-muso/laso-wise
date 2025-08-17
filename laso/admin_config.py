from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from django.shortcuts import redirect


class EnhancedAdminSite(AdminSite):
    site_header = "LASO Medical System Administration"
    site_title = "LASO Admin"
    index_title = "Welcome to LASO Medical System"
    
    def index(self, request, extra_context=None):
        """Override the default admin index to redirect to enhanced dashboard"""
        if request.user.is_superuser:
            return redirect('core:enhanced-admin-dashboard')
        return super().index(request, extra_context)
    
    def get_app_list(self, request):
        """Customize the app list to add quick links"""
        app_list = super().get_app_list(request)
        
        # Add custom dashboard link
        custom_app = {
            'name': 'System Analytics',
            'app_label': 'analytics',
            'models': [
                {
                    'name': 'Enhanced Dashboard',
                    'object_name': 'dashboard',
                    'admin_url': reverse('core:enhanced-admin-dashboard'),
                    'view_only': True,
                },
                {
                    'name': 'Vitals Analytics',
                    'object_name': 'vitals',
                    'admin_url': '/admin/vitals/vitalrecord/',
                    'view_only': True,
                },
                {
                    'name': 'Telemedicine Config',
                    'object_name': 'telemedicine',
                    'admin_url': '/admin/telemedicine/videoproviderconfig/',
                    'view_only': True,
                }
            ]
        }
        app_list.insert(0, custom_app)
        
        return app_list


# Replace the default admin site
admin.site = EnhancedAdminSite()
admin.sites.site = admin.site