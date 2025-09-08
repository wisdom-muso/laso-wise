from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models_ai_config import AIConfiguration, AIConversation, AIPromptTemplate


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'model_name', 'is_active', 'is_default', 
        'max_tokens', 'temperature', 'created_at'
    ]
    list_filter = ['provider', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'provider', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider', 'is_active', 'is_default')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_url', 'model_name'),
            'description': 'API credentials and endpoint configuration'
        }),
        ('Model Parameters', {
            'fields': ('max_tokens', 'temperature'),
            'description': 'Parameters that control AI model behavior'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for different providers
        if 'provider' in form.base_fields:
            form.base_fields['provider'].help_text = mark_safe("""
            <ul>
                <li><strong>OpenAI:</strong> Use official OpenAI API (requires OpenAI API key)</li>
                <li><strong>OpenRouter:</strong> Access multiple models through OpenRouter (requires OpenRouter API key)</li>
                <li><strong>Hugging Face:</strong> Use Hugging Face models (requires HF API key)</li>
                <li><strong>Anthropic:</strong> Use Claude models (requires Anthropic API key)</li>
                <li><strong>Google AI:</strong> Use Google AI models (requires Google AI API key)</li>
            </ul>
            """)
        
        if 'api_key' in form.base_fields:
            form.base_fields['api_key'].widget.attrs.update({
                'style': 'width: 100%; font-family: monospace;',
                'placeholder': 'Enter your API key here...'
            })
        
        return form
    
    def save_model(self, request, obj, form, change):
        # Ensure only one default configuration
        if obj.is_default:
            AIConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save_model(request, obj, form, change)
    
    actions = ['make_default', 'activate_configs', 'deactivate_configs']
    
    def make_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one configuration to make default.", level='error')
            return
        
        AIConfiguration.objects.filter(is_default=True).update(is_default=False)
        queryset.update(is_default=True, is_active=True)
        self.message_user(request, "Configuration set as default.")
    make_default.short_description = "Set as default configuration"
    
    def activate_configs(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} configurations activated.")
    activate_configs.short_description = "Activate selected configurations"
    
    def deactivate_configs(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} configurations deactivated.")
    deactivate_configs.short_description = "Deactivate selected configurations"


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_id', 'message_preview', 'response_preview', 
        'ai_config', 'tokens_used', 'response_time', 'created_at'
    ]
    list_filter = ['ai_config', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'message', 'session_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = "Message"
    
    def response_preview(self, obj):
        return obj.response[:50] + "..." if len(obj.response) > 50 else obj.response
    response_preview.short_description = "Response"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'ai_config')
    
    fieldsets = (
        ('Conversation Details', {
            'fields': ('user', 'session_id', 'message', 'response')
        }),
        ('AI Information', {
            'fields': ('ai_config', 'tokens_used', 'response_time')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def has_add_permission(self, request):
        return False  # Conversations are created automatically
    
    actions = ['export_conversations']
    
    def export_conversations(self, request, queryset):
        # This could be enhanced to export conversations to CSV/JSON
        self.message_user(request, f"Export functionality for {queryset.count()} conversations (to be implemented).")
    export_conversations.short_description = "Export selected conversations"


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'prompt_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Prompt Template', {
            'fields': ('prompt_template',),
            'description': 'Use placeholders like {symptom}, {patient_age}, {medical_history} in your template'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if 'prompt_template' in form.base_fields:
            form.base_fields['prompt_template'].widget.attrs.update({
                'rows': 10,
                'style': 'width: 100%; font-family: monospace;',
                'placeholder': 'Enter your prompt template here...\n\nExample:\nAnalyze the following symptoms: {symptom}\nPatient age: {patient_age}\nMedical history: {medical_history}\n\nProvide a professional medical assessment.'
            })
        
        return form


# Custom admin site configuration
class AIAdminConfig:
    """
    Configuration class for AI-related admin settings
    """
    
    @staticmethod
    def customize_admin_site(admin_site):
        """
        Customize the admin site for AI features
        """
        admin_site.site_header = "Laso Healthcare - AI Configuration"
        admin_site.site_title = "AI Admin"
        admin_site.index_title = "AI Assistant Management"
    
    @staticmethod
    def get_ai_status():
        """
        Get current AI configuration status
        """
        active_configs = AIConfiguration.objects.filter(is_active=True).count()
        default_config = AIConfiguration.objects.filter(is_default=True).first()
        total_conversations = AIConversation.objects.count()
        
        return {
            'active_configs': active_configs,
            'default_provider': default_config.get_provider_display() if default_config else 'None',
            'total_conversations': total_conversations
        }