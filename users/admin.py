from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Information'), {'fields': ('first_name', 'last_name', 'email', 'user_type')}),
        (_('Doctor Information'), {'fields': ('specialization',), 'classes': ('collapse',)}),
        (_('Patient Information'), {'fields': ('date_of_birth', 'phone_number', 'address', 'blood_type'), 'classes': ('collapse',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'user_type'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

admin.site.register(User, CustomUserAdmin)
