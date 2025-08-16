from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json

from accounts.models import User
from bookings.models import Booking
from vitals.models import VitalRecord, VitalCategory
from telemedicine.models import Consultation, VideoProviderConfig
from core.models import HospitalSettings


def is_superuser(user):
    return user.is_superuser


@method_decorator(user_passes_test(is_superuser), name='dispatch')
class EnhancedAdminDashboardView(TemplateView):
    template_name = 'admin/enhanced_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range for analytics
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Basic stats
        context.update({
            'total_patients': User.objects.filter(role='patient').count(),
            'total_doctors': User.objects.filter(role='doctor').count(),
            'total_appointments': Booking.objects.count(),
            'pending_appointments': Booking.objects.filter(status='pending').count(),
            'active_consultations': Consultation.objects.filter(status='in_progress').count(),
        })
        
        # Vitals analytics (inline)
        context.update(self.get_vitals_analytics(start_date, end_date))
        
        # Telemedicine analytics
        context.update(self.get_telemedicine_analytics(start_date, end_date))
        
        # System configuration
        context.update(self.get_system_config())
        
        return context
    
    def get_vitals_analytics(self, start_date, end_date):
        """Get vitals analytics for inline display"""
        vital_records = VitalRecord.objects.filter(
            recorded_at__range=[start_date, end_date]
        )
        
        # Vitals by category
        vitals_by_category = []
        for category in VitalCategory.objects.filter(is_active=True):
            records = vital_records.filter(category=category)
            avg_value = records.aggregate(avg=Avg('value'))['avg']
            count = records.count()
            
            # Determine status based on normal ranges
            status = 'normal'
            if avg_value and category.min_normal and category.max_normal:
                if avg_value < category.min_normal or avg_value > category.max_normal:
                    status = 'abnormal'
            
            vitals_by_category.append({
                'name': category.name,
                'unit': category.unit,
                'count': count,
                'avg_value': round(avg_value, 2) if avg_value else 0,
                'status': status,
                'normal_range': f"{category.min_normal}-{category.max_normal}" if category.min_normal and category.max_normal else "N/A"
            })
        
        # Recent critical vitals
        critical_vitals = []
        for record in vital_records.order_by('-recorded_at')[:10]:
            if record.category.min_normal and record.category.max_normal:
                if record.value < record.category.min_normal or record.value > record.category.max_normal:
                    critical_vitals.append({
                        'patient': record.patient.get_full_name(),
                        'category': record.category.name,
                        'value': record.value,
                        'unit': record.category.unit,
                        'recorded_at': record.recorded_at,
                        'severity': 'high' if (record.value < record.category.min_normal * 0.8 or 
                                            record.value > record.category.max_normal * 1.2) else 'medium'
                    })
        
        return {
            'vitals_summary': {
                'total_records': vital_records.count(),
                'categories_tracked': VitalCategory.objects.filter(is_active=True).count(),
                'avg_readings_per_day': round(vital_records.count() / 30, 1),
                'professional_readings': vital_records.filter(is_professional_reading=True).count(),
            },
            'vitals_by_category': vitals_by_category,
            'critical_vitals': critical_vitals,
        }
    
    def get_telemedicine_analytics(self, start_date, end_date):
        """Get telemedicine analytics"""
        consultations = Consultation.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        # Consultation stats
        consultation_stats = {
            'total': consultations.count(),
            'completed': consultations.filter(status='completed').count(),
            'in_progress': consultations.filter(status='in_progress').count(),
            'cancelled': consultations.filter(status='cancelled').count(),
            'avg_duration': consultations.filter(
                duration_minutes__isnull=False
            ).aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
        }
        
        # Provider distribution
        provider_stats = consultations.values('video_provider').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'consultation_stats': consultation_stats,
            'provider_stats': list(provider_stats),
            'video_providers': VideoProviderConfig.objects.filter(is_active=True),
        }
    
    def get_system_config(self):
        """Get system configuration info"""
        hospital_settings = HospitalSettings.objects.first()
        video_configs = VideoProviderConfig.objects.all()
        
        return {
            'hospital_settings': hospital_settings,
            'video_configs': video_configs,
            'system_health': {
                'database_connections': 'healthy',  # This could be a real check
                'api_endpoints': 'healthy',
                'file_storage': 'healthy',
            }
        }


@user_passes_test(is_superuser)
def vitals_analytics_api(request):
    """API endpoint for vitals analytics data"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Daily vitals count
    daily_data = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        count = VitalRecord.objects.filter(
            recorded_at__date=current_date
        ).count()
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count
        })
        current_date += timedelta(days=1)
    
    # Category distribution
    category_data = list(
        VitalRecord.objects.filter(
            recorded_at__range=[start_date, end_date]
        ).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
    )
    
    return JsonResponse({
        'daily_data': daily_data,
        'category_data': category_data,
    })


@user_passes_test(is_superuser)
def telemedicine_config_api(request):
    """API endpoint for telemedicine configuration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            provider = data.get('provider')
            config_data = data.get('config', {})
            
            config, created = VideoProviderConfig.objects.get_or_create(
                provider=provider,
                defaults=config_data
            )
            
            if not created:
                for key, value in config_data.items():
                    setattr(config, key, value)
                config.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{provider} configuration saved successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    # GET request - return current configurations
    configs = {}
    for config in VideoProviderConfig.objects.all():
        configs[config.provider] = {
            'is_active': config.is_active,
            'max_participants': config.max_participants,
            'recording_enabled': config.recording_enabled,
            'api_key': config.api_key[:10] + '...' if config.api_key else '',
            'has_api_secret': bool(config.api_secret),
        }
    
    return JsonResponse(configs)