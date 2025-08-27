from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from treatments.models import Treatment

class MedicalImage(models.Model):
    """
    Medical image model. Represents images like X-ray, MRI, CT scans.
    """
    IMAGE_TYPE_CHOICES = [
        ('xray', _('Röntgen')),
        ('mri', _('MR')),
        ('ct', _('BT (Bilgisayarlı Tomografi)')),
        ('ultrasound', _('Ultrason')),
        ('other', _('Diğer')),
    ]
    
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='medical_images',
        verbose_name=_('Treatment')
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_images',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordered_medical_images',
        verbose_name=_('Requesting Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        verbose_name=_('Image Type')
    )
    body_part = models.CharField(
        max_length=100,
        verbose_name=_('Body Region')
    )
    image_file = models.ImageField(
        upload_to='medical_images/',
        verbose_name=_('Image File')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Açıklama')
    )
    taken_date = models.DateField(
        verbose_name=_('Çekim Tarihi')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Oluşturulma Tarihi')
    )
    
    class Meta:
        verbose_name = _('Medical Image')
        verbose_name_plural = _('Medical Images')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.get_image_type_display()} - {self.body_part}"

class Report(models.Model):
    """
    Rapor modeli. Doktorlar tarafından oluşturulan raporları temsil eder.
    """
    REPORT_TYPE_CHOICES = [
        ('diagnostic', _('Tanı Raporu')),
        ('progress', _('İlerleme Raporu')),
        ('discharge', _('Taburcu Raporu')),
        ('consultation', _('Konsültasyon Raporu')),
        ('sick_leave', _('İş Göremezlik Raporu')),
        ('other', _('Diğer')),
    ]
    
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Tedavi')
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Hasta'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='written_reports',
        verbose_name=_('Raporu Yazan Doktor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_('Rapor Tipi')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Rapor Başlığı')
    )
    content = models.TextField(
        verbose_name=_('Rapor İçeriği')
    )
    valid_from = models.DateField(
        verbose_name=_('Geçerlilik Başlangıcı')
    )
    valid_until = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Geçerlilik Sonu')
    )
    report_file = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True,
        verbose_name=_('Rapor Dosyası')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Oluşturulma Tarihi')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Güncellenme Tarihi')
    )
    
    class Meta:
        verbose_name = _('Rapor')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.title} - {self.valid_from}"
