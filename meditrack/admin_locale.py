"""
Django Admin Interface Locale Configuration
Ensures admin interface displays in English
"""

from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class EnglishAdminConfig(AdminConfig):
    """Custom Admin Configuration to force English interface"""
    default_site = 'meditrack.admin_locale.EnglishAdminSite'


class EnglishAdminSite(admin.AdminSite):
    """Custom Admin Site with English labels"""
    
    site_header = _('Laso Healthcare - Clinical Management System')
    site_title = _('Laso Healthcare Admin')
    index_title = _('Clinical Management Dashboard')
    
    def __init__(self, name='admin'):
        super().__init__(name)
        
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site with English labels.
        """
        app_dict = self._build_app_dict(request)
        
        # Custom app labeling for better English interface
        app_translations = {
            'Users': 'User Management',
            'Appointments': 'Appointment Management', 
            'Treatments': 'Treatment & Medical Records',
            'Core': 'Core System',
            'Telemedicine': 'Telemedicine Sessions',
        }
        
        for app in app_dict.values():
            if app['name'] in app_translations:
                app['name'] = app_translations[app['name']]
                
        # Sort the apps alphabetically
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        
        return app_list


# Create the custom admin site instance
admin_site = EnglishAdminSite(name='admin')