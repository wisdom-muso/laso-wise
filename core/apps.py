from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    
    def ready(self):
        # Configure Django admin site after all apps are loaded
        from django.contrib import admin
        from django.conf import settings
        
        # Set admin site configuration
        admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Laso Digital Health Administration')
        admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Laso Digital Health Admin Portal')
        admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Welcome to Laso Digital Health Admin Portal')
