"""
Internationalization Management for Laso Healthcare
Multi-language support management
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import json


class Language(models.Model):
    """
    Supported languages
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('Language Code'),
        help_text=_('ISO 639-1 language code (e.g: tr, en, de)')
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Language Name')
    )
    
    native_name = models.CharField(
        max_length=100,
        verbose_name=_('Native Name'),
        help_text=_('Name of the language in its own language')
    )
    
    flag_emoji = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Flag Emoji')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
    )
    
    is_rtl = models.BooleanField(
        default=False,
        verbose_name=_('Right to Left?'),
        help_text=_('For languages like Arabic, Hebrew')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order')
    )
    
    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.flag_emoji} {self.native_name}"


class UserLanguagePreference(models.Model):
    """
    User language preferences
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='language_preference',
        verbose_name=_('User')
    )
    
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        verbose_name=_('Preferred Language')
    )
    
    date_format = models.CharField(
        max_length=20,
        choices=[
            ('DD/MM/YYYY', 'DD/MM/YYYY'),
            ('MM/DD/YYYY', 'MM/DD/YYYY'),
            ('YYYY-MM-DD', 'YYYY-MM-DD'),
            ('DD.MM.YYYY', 'DD.MM.YYYY'),
        ],
        default='DD/MM/YYYY',
        verbose_name=_('Date Format')
    )
    
    time_format = models.CharField(
        max_length=10,
        choices=[
            ('24h', '24 Hour (14:30)'),
            ('12h', '12 Hour (2:30 PM)'),
        ],
        default='24h',
        verbose_name=_('Time Format')
    )
    
    timezone = models.CharField(
        max_length=50,
        default='Europe/Istanbul',
        verbose_name=_('Timezone')
    )
    
    number_format = models.CharField(
        max_length=20,
        choices=[
            ('1,234.56', '1,234.56 (Anglo-Saxon)'),
            ('1.234,56', '1.234,56 (Continental European)'),
            ('1 234,56', '1 234,56 (French)'),
        ],
        default='1,234.56',
        verbose_name=_('Number Format')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('User Language Preference')
        verbose_name_plural = _('User Language Preferences')
    
    def __str__(self):
        return f"{self.user} - {self.language}"


class TranslationContext(models.Model):
    """
    Translation contexts - special translations for medical terms
    """
    CONTEXT_TYPES = [
        ('medical', _('Medical Terms')),
        ('ui', _('User Interface')),
        ('notification', _('Notifications')),
        ('report', _('Reports')),
        ('appointment', _('Appointment')),
        ('treatment', _('Treatment')),
        ('medication', _('Medication')),
        ('diagnosis', _('Diagnosis')),
    ]
    
    context_type = models.CharField(
        max_length=20,
        choices=CONTEXT_TYPES,
        verbose_name=_('Context Type')
    )
    
    source_text = models.TextField(
        verbose_name=_('Source Text'),
        help_text=_('Original text to be translated')
    )
    
    context_key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Context Key'),
        help_text=_('Unique key (e.g.: diagnosis.diabetes)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description for translators')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Translation Context')
        verbose_name_plural = _('Translation Contexts')
        ordering = ['context_type', 'context_key']
    
    def __str__(self):
        return f"{self.context_type} - {self.context_key}"


class Translation(models.Model):
    """
    Translations
    """
    context = models.ForeignKey(
        TranslationContext,
        on_delete=models.CASCADE,
        related_name='translations',
        verbose_name=_('Context')
    )
    
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        verbose_name=_('Language')
    )
    
    translated_text = models.TextField(
        verbose_name=_('Translated Text')
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('Is Approved?')
    )
    
    translator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Translator')
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_translations',
        verbose_name=_('Reviewer')
    )
    
    quality_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Quality Score'),
        help_text=_('Quality score from 1-5')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Notes about the translation')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        unique_together = ['context', 'language']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.context.context_key} - {self.language.code}"


class MedicalTerminology(models.Model):
    """
    Medical terminology dictionary
    """
    CATEGORY_CHOICES = [
        ('anatomy', _('Anatomy')),
        ('disease', _('Disease')),
        ('symptom', _('Symptom')),
        ('medication', _('Medication')),
        ('procedure', _('Procedure')),
        ('test', _('Test/Analysis')),
        ('specialty', _('Specialty')),
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_('Category')
    )
    
    term_en = models.CharField(
        max_length=200,
        verbose_name=_('English Term')
    )
    
    term_tr = models.CharField(
        max_length=200,
        verbose_name=_('Turkish Term')
    )
    
    definition_en = models.TextField(
        blank=True,
        verbose_name=_('English Definition')
    )
    
    definition_tr = models.TextField(
        blank=True,
        verbose_name=_('Turkish Definition')
    )
    
    synonyms = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Synonyms'),
        help_text=_('{"en": ["synonym1", "synonym2"], "tr": ["eşanlamlı1"]}')
    )
    
    icd_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('ICD Code'),
        help_text=_('ICD-10 code for diseases')
    )
    
    is_commonly_used = models.BooleanField(
        default=False,
        verbose_name=_('Is Commonly Used?')
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Usage Count')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Medical Terminology')
        verbose_name_plural = _('Medical Terminologies')
        ordering = ['category', 'term_en']
        indexes = [
            models.Index(fields=['term_en']),
            models.Index(fields=['term_tr']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.term_en} / {self.term_tr}"
    
    def increment_usage(self):
        """Kullanım sayısını artır"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class LocalizationSetting(models.Model):
    """
    Lokalizasyon ayarları
    """
    language = models.OneToOneField(
        Language,
        on_delete=models.CASCADE,
        related_name='localization_settings',
        verbose_name=_('Language')
    )
    
    # Medikal birimler
    temperature_unit = models.CharField(
        max_length=10,
        choices=[
            ('celsius', '°C (Celsius)'),
            ('fahrenheit', '°F (Fahrenheit)'),
        ],
        default='celsius',
        verbose_name=_('Sıcaklık Birimi')
    )
    
    weight_unit = models.CharField(
        max_length=10,
        choices=[
            ('kg', 'Kilogram (kg)'),
            ('lb', 'Pound (lb)'),
        ],
        default='kg',
        verbose_name=_('Ağırlık Birimi')
    )
    
    height_unit = models.CharField(
        max_length=10,
        choices=[
            ('cm', 'Santimetre (cm)'),
            ('ft_in', 'Feet & Inches'),
        ],
        default='cm',
        verbose_name=_('Boy Birimi')
    )
    
    blood_pressure_unit = models.CharField(
        max_length=10,
        choices=[
            ('mmhg', 'mmHg'),
            ('kpa', 'kPa'),
        ],
        default='mmhg',
        verbose_name=_('Tansiyon Birimi')
    )
    
    # Adres formatı
    address_format = models.TextField(
        default='',
        verbose_name=_('Adres Formatı'),
        help_text=_('Adres gösterim formatı şablonu')
    )
    
    # Para birimi
    currency_code = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Para Birimi Kodu')
    )
    
    currency_symbol = models.CharField(
        max_length=5,
        default='₺',
        verbose_name=_('Para Birimi Sembolü')
    )
    
    # Tarih ve saat formatları
    date_format_short = models.CharField(
        max_length=20,
        default='dd/mm/yyyy',
        verbose_name=_('Kısa Tarih Formatı')
    )
    
    date_format_long = models.CharField(
        max_length=50,
        default='dd mmmm yyyy',
        verbose_name=_('Uzun Tarih Formatı')
    )
    
    time_format = models.CharField(
        max_length=20,
        default='HH:mm',
        verbose_name=_('Saat Formatı')
    )
    
    first_day_of_week = models.IntegerField(
        choices=[
            (0, _('Pazar')),
            (1, _('Pazartesi')),
        ],
        default=1,
        verbose_name=_('Haftanın İlk Günü')
    )
    
    class Meta:
        verbose_name = _('Lokalizasyon Ayarı')
        verbose_name_plural = _('Lokalizasyon Ayarları')
    
    def __str__(self):
        return f"{self.language} - Lokalizasyon Ayarları"
