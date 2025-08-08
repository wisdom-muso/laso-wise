from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDay
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import json
import time
import random
from datetime import timedelta

from accounts.decorators import AdminRequiredMixin
from .models import SyncStatus, SystemHealthCheck, DataSyncLog
from .utils import perform_health_check, trigger_sync_operation


class SyncDashboardView(AdminRequiredMixin, ListView):
    """
    Dashboard view for sync operations and system health
    """
    model = SyncStatus
    template_name = 'sync_monitor/dashboard.html'
    context_object_name = 'sync_operations'
    paginate_by = 10
    
    def get_queryset(self):
        return SyncStatus.objects.all().order_by('-started_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get latest health checks
        context['health_checks'] = SystemHealthCheck.objects.filter(
            check_type='overall'
        ).order_by('-checked_at')[:5]
        
        # Get component health status
        component_health = {}
        for component in ['database', 'api', 'storage', 'cache', 'queue']:
            latest_check = SystemHealthCheck.objects.filter(
                check_type=component
            ).order_by('-checked_at').first()
            
            if latest_check:
                component_health[component] = {
                    'status': latest_check.status,
                    'response_time': latest_check.response_time,
                    'checked_at': latest_check.checked_at,
                    'details': latest_check.details
                }
            else:
                component_health[component] = {
                    'status': 'unknown',
                    'response_time': 0,
                    'checked_at': None,
                    'details': 'No health check performed yet'
                }
        
        context['component_health'] = component_health
        
        # Get sync statistics
        context['sync_stats'] = {
            'total': SyncStatus.objects.count(),
            'completed': SyncStatus.objects.filter(status='completed').count(),
            'failed': SyncStatus.objects.filter(status='failed').count(),
            'in_progress': SyncStatus.objects.filter(status='in_progress').count(),
            'pending': SyncStatus.objects.filter(status='pending').count(),
        }
        
        # Get latest sync operation for each type
        latest_syncs = {}
        for sync_type, _ in SyncStatus.SYNC_TYPE_CHOICES:
            latest = SyncStatus.objects.filter(
                sync_type=sync_type
            ).order_by('-started_at').first()
            
            if latest:
                latest_syncs[sync_type] = latest
        
        context['latest_syncs'] = latest_syncs
        
        # Get sync history data for charts
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        sync_history = SyncStatus.objects.filter(
            started_at__range=[start_date, end_date]
        ).annotate(
            day=TruncDay('started_at')
        ).values('day', 'status').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Format for chart
        chart_data = {
            'labels': [],
            'completed': [],
            'failed': [],
            'in_progress': [],
            'pending': []
        }
        
        # Initialize with zeros
        current_date = start_date
        while current_date <= end_date:
            chart_data['labels'].append(current_date.strftime('%Y-%m-%d'))
            chart_data['completed'].append(0)
            chart_data['failed'].append(0)
            chart_data['in_progress'].append(0)
            chart_data['pending'].append(0)
            current_date += timedelta(days=1)
        
        # Fill in actual data
        for entry in sync_history:
            day_str = entry['day'].strftime('%Y-%m-%d')
            if day_str in chart_data['labels']:
                idx = chart_data['labels'].index(day_str)
                chart_data[entry['status']][idx] = entry['count']
        
        context['chart_data'] = json.dumps(chart_data)
        
        return context


class SyncStatusDetailView(AdminRequiredMixin, DetailView):
    """
    Detail view for a sync operation
    """
    model = SyncStatus
    template_name = 'sync_monitor/sync_detail.html'
    context_object_name = 'sync_operation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get logs for this sync operation
        context['logs'] = self.object.logs.all().order_by('-timestamp')
        
        # Calculate success rate by entity type
        entity_stats = self.object.logs.values('entity_type').annotate(
            total=Count('id'),
            success_count=Count('id', filter=Q(success=True)),
            failure_count=Count('id', filter=Q(success=False))
        ).order_by('entity_type')
        
        for stat in entity_stats:
            if stat['total'] > 0:
                stat['success_rate'] = round((stat['success_count'] / stat['total']) * 100, 2)
            else:
                stat['success_rate'] = 0
        
        context['entity_stats'] = entity_stats
        
        return context


class TriggerSyncView(AdminRequiredMixin, View):
    """
    View to trigger a new sync operation
    """
    def post(self, request, *args, **kwargs):
        sync_type = request.POST.get('sync_type')
        
        if not sync_type:
            messages.error(request, _('Sync type is required'))
            return redirect('sync_monitor:dashboard')
        
        # Create a new sync operation
        sync_operation = SyncStatus.objects.create(
            sync_type=sync_type,
            status='pending',
            initiated_by=request.user
        )
        
        # Trigger the sync operation (this would normally be done asynchronously)
        try:
            # For demo purposes, we'll simulate the sync operation
            trigger_sync_operation(sync_operation.id)
            messages.success(request, _('Sync operation triggered successfully'))
        except Exception as e:
            sync_operation.mark_failed(str(e))
            messages.error(request, _('Failed to trigger sync operation: {}').format(str(e)))
        
        return redirect('sync_monitor:dashboard')


class PerformHealthCheckView(AdminRequiredMixin, View):
    """
    View to trigger a system health check
    """
    def post(self, request, *args, **kwargs):
        check_type = request.POST.get('check_type', 'overall')
        
        try:
            # Perform the health check
            perform_health_check(check_type)
            messages.success(request, _('Health check performed successfully'))
        except Exception as e:
            messages.error(request, _('Failed to perform health check: {}').format(str(e)))
        
        return redirect('sync_monitor:dashboard')


class SystemHealthHistoryView(AdminRequiredMixin, ListView):
    """
    View to display system health history
    """
    model = SystemHealthCheck
    template_name = 'sync_monitor/health_history.html'
    context_object_name = 'health_checks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SystemHealthCheck.objects.all()
        
        # Filter by check type if provided
        check_type = self.request.GET.get('check_type')
        if check_type:
            queryset = queryset.filter(check_type=check_type)
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-checked_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['check_types'] = SystemHealthCheck.CHECK_TYPE_CHOICES
        context['statuses'] = SystemHealthCheck.STATUS_CHOICES
        
        # Add selected filters
        context['selected_check_type'] = self.request.GET.get('check_type', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        return context


class SystemHealthAPIView(AdminRequiredMixin, View):
    """
    API view to get system health data for real-time updates
    """
    def get(self, request, *args, **kwargs):
        # Get latest health checks for each component
        components = {}
        for component in ['database', 'api', 'storage', 'cache', 'queue', 'overall']:
            latest_check = SystemHealthCheck.objects.filter(
                check_type=component
            ).order_by('-checked_at').first()
            
            if latest_check:
                components[component] = {
                    'status': latest_check.status,
                    'response_time': latest_check.response_time,
                    'checked_at': latest_check.checked_at.isoformat(),
                    'details': latest_check.details
                }
            else:
                components[component] = {
                    'status': 'unknown',
                    'response_time': 0,
                    'checked_at': None,
                    'details': 'No health check performed yet'
                }
        
        # Get in-progress sync operations
        in_progress_syncs = []
        for sync in SyncStatus.objects.filter(status='in_progress'):
            in_progress_syncs.append({
                'id': sync.id,
                'sync_type': sync.get_sync_type_display(),
                'started_at': sync.started_at.isoformat(),
                'records_processed': sync.records_processed,
                'records_failed': sync.records_failed,
                'duration': str(sync.duration()).split('.')[0] if sync.duration() else '0:00:00'
            })
        
        return JsonResponse({
            'components': components,
            'in_progress_syncs': in_progress_syncs,
            'timestamp': timezone.now().isoformat()
        })