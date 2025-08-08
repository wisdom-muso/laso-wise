import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import SyncStatus, SystemHealthCheck


class SyncStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time sync status updates
    """
    async def connect(self):
        """
        Connect to the WebSocket and join the sync_status group
        """
        self.group_name = 'sync_status'
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        initial_data = await self.get_initial_data()
        await self.send(text_data=json.dumps(initial_data))
    
    async def disconnect(self, close_code):
        """
        Leave the sync_status group
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'get_sync_status':
            # Send sync status data
            sync_data = await self.get_sync_status_data()
            await self.send(text_data=json.dumps(sync_data))
        
        elif message_type == 'get_health_status':
            # Send health status data
            health_data = await self.get_health_status_data()
            await self.send(text_data=json.dumps(health_data))
    
    async def sync_status_update(self, event):
        """
        Receive sync status update from group and send to WebSocket
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))
    
    async def health_status_update(self, event):
        """
        Receive health status update from group and send to WebSocket
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_initial_data(self):
        """
        Get initial data for the WebSocket connection
        """
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
        
        return {
            'type': 'initial_data',
            'components': components,
            'in_progress_syncs': in_progress_syncs,
            'timestamp': timezone.now().isoformat()
        }
    
    @database_sync_to_async
    def get_sync_status_data(self):
        """
        Get sync status data
        """
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
        
        return {
            'type': 'sync_status_update',
            'in_progress_syncs': in_progress_syncs,
            'timestamp': timezone.now().isoformat()
        }
    
    @database_sync_to_async
    def get_health_status_data(self):
        """
        Get health status data
        """
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
        
        return {
            'type': 'health_status_update',
            'components': components,
            'timestamp': timezone.now().isoformat()
        }