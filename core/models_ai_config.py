from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class AIConfiguration(models.Model):
    """
    AI Configuration model for storing API keys and settings
    """
    
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('openrouter', 'OpenRouter'),
        ('huggingface', 'Hugging Face'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google AI'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Configuration Name'),
        help_text=_('A descriptive name for this AI configuration')
    )
    
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        verbose_name=_('AI Provider'),
        help_text=_('The AI service provider')
    )
    
    api_key = models.CharField(
        max_length=500,
        verbose_name=_('API Key'),
        help_text=_('The API key for the AI service')
    )
    
    api_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        verbose_name=_('API URL'),
        help_text=_('Custom API URL (optional, for services like OpenRouter)')
    )
    
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Model Name'),
        help_text=_('Specific model to use (e.g., gpt-4, claude-3, etc.)')
    )
    
    max_tokens = models.PositiveIntegerField(
        default=1000,
        verbose_name=_('Max Tokens'),
        help_text=_('Maximum number of tokens in the response')
    )
    
    temperature = models.FloatField(
        default=0.7,
        verbose_name=_('Temperature'),
        help_text=_('Controls randomness in responses (0.0 to 1.0)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Whether this configuration is currently active')
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Is Default'),
        help_text=_('Whether this is the default configuration to use')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('AI Configuration')
        verbose_name_plural = _('AI Configurations')
        ordering = ['-is_default', '-is_active', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default configuration
        if self.is_default:
            AIConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_config(cls):
        """Get the default AI configuration"""
        return cls.objects.filter(is_active=True, is_default=True).first()
    
    @classmethod
    def get_active_configs(cls):
        """Get all active AI configurations"""
        return cls.objects.filter(is_active=True)


class AIConversation(models.Model):
    """
    Model to store AI conversation history
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('User')
    )
    
    session_id = models.CharField(
        max_length=100,
        verbose_name=_('Session ID'),
        help_text=_('Unique identifier for the conversation session')
    )
    
    message = models.TextField(
        verbose_name=_('User Message'),
        help_text=_('The message sent by the user')
    )
    
    response = models.TextField(
        verbose_name=_('AI Response'),
        help_text=_('The response from the AI')
    )
    
    ai_config = models.ForeignKey(
        AIConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('AI Configuration'),
        help_text=_('The AI configuration used for this response')
    )
    
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tokens Used'),
        help_text=_('Number of tokens used for this interaction')
    )
    
    response_time = models.FloatField(
        default=0.0,
        verbose_name=_('Response Time'),
        help_text=_('Time taken to generate the response (in seconds)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('AI Conversation')
        verbose_name_plural = _('AI Conversations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class AIPromptTemplate(models.Model):
    """
    Model for storing AI prompt templates
    """
    
    TEMPLATE_TYPES = [
        ('symptom_analysis', 'Symptom Analysis'),
        ('drug_interaction', 'Drug Interaction Check'),
        ('general_health', 'General Health Advice'),
        ('medical_history', 'Medical History Analysis'),
        ('treatment_recommendation', 'Treatment Recommendation'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Template Name')
    )
    
    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPES,
        verbose_name=_('Template Type')
    )
    
    prompt_template = models.TextField(
        verbose_name=_('Prompt Template'),
        help_text=_('The prompt template with placeholders like {symptom}, {patient_age}, etc.')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('AI Prompt Template')
        verbose_name_plural = _('AI Prompt Templates')
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"