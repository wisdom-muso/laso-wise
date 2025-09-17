#!/usr/bin/env python3
"""
Script to fix Turkish verbose names in telemedicine models
"""

import re

# Read the telemedicine models file
with open('telemedicine/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Turkish to English mappings for verbose names
replacements = {
    # TelemedDocument
    "verbose_name=_('Randevu')": "verbose_name=_('Appointment')",
    "verbose_name=_('Başlık')": "verbose_name=_('Title')",
    "verbose_name=_('Belge Türü')": "verbose_name=_('Document Type')",
    "verbose_name=_('Dosya')": "verbose_name=_('File')",
    "verbose_name=_('Açıklama')": "verbose_name=_('Description')",
    "verbose_name=_('Yükleyen')": "verbose_name=_('Uploaded By')",
    "verbose_name=_('Oluşturulma Tarihi')": "verbose_name=_('Created At')",
    "verbose_name = _('Tele-tıp Belgesi')": "verbose_name = _('Telemedicine Document')",
    "verbose_name_plural = _('Tele-tıp Belgeleri')": "verbose_name_plural = _('Telemedicine Documents')",
    
    # TelemedPrescription
    "verbose_name=_('İlaçlar')": "verbose_name=_('Medications')",
    "verbose_name=_('Talimatlar')": "verbose_name=_('Instructions')",
    "verbose_name=_('Süre (gün)')": "verbose_name=_('Duration (days)')",
    "verbose_name=_('Yenilenebilir mi?')": "verbose_name=_('Renewable?')",
    "verbose_name=_('Oluşturan Doktor')": "verbose_name=_('Prescribing Doctor')",
    "verbose_name = _('Tele-tıp Reçetesi')": "verbose_name = _('Telemedicine Prescription')",
    "verbose_name_plural = _('Tele-tıp Reçeteleri')": "verbose_name_plural = _('Telemedicine Prescriptions')",
    
    # TelemedNote
    "verbose_name=_('İçerik')": "verbose_name=_('Content')",
    "verbose_name=_('Not Türü')": "verbose_name=_('Note Type')",
    "verbose_name=_('Özel Not mu?')": "verbose_name=_('Private Note?')",
    "verbose_name=_('Güncellenme Tarihi')": "verbose_name=_('Updated At')",
    "verbose_name = _('Tele-tıp Notu')": "verbose_name = _('Telemedicine Note')",
    "verbose_name_plural = _('Tele-tıp Notları')": "verbose_name_plural = _('Telemedicine Notes')",
    
    # TeleMedicineConsultation
    "verbose_name=_('Konsültasyon Türü')": "verbose_name=_('Consultation Type')",
    "verbose_name=_('Toplantı ID')": "verbose_name=_('Meeting ID')",
    "verbose_name=_('Toplantı URL\\'si')": "verbose_name=_('Meeting URL')",
    "verbose_name=_('Toplantı Şifresi')": "verbose_name=_('Meeting Password')",
    "verbose_name=_('Planlanan Başlangıç')": "verbose_name=_('Scheduled Start')",
    "verbose_name=_('Gerçek Başlangıç')": "verbose_name=_('Actual Start')",
    "verbose_name=_('Bitiş Zamanı')": "verbose_name=_('End Time')",
    "verbose_name=_('Süre (Dakika)')": "verbose_name=_('Duration (Minutes)')",
    "verbose_name=_('Doktor Katılım Zamanı')": "verbose_name=_('Doctor Join Time')",
    "verbose_name=_('Hasta Katılım Zamanı')": "verbose_name=_('Patient Join Time')",
    "verbose_name=_('Teknik Sorunlar')": "verbose_name=_('Technical Issues')",
    "verbose_name=_('Konsültasyon Notları')": "verbose_name=_('Consultation Notes')",
    "verbose_name=_('Hasta Geri Bildirimi')": "verbose_name=_('Patient Feedback')",
    "verbose_name=_('Doktor Geri Bildirimi')": "verbose_name=_('Doctor Feedback')",
    "verbose_name=_('Hasta Değerlendirmesi (1-5)')": "verbose_name=_('Patient Rating (1-5)')",
    "verbose_name=_('Doktor Değerlendirmesi (1-5)')": "verbose_name=_('Doctor Rating (1-5)')",
    "verbose_name=_('Kayıt Yapıldı mı?')": "verbose_name=_('Recording Made?')",
    "verbose_name=_('Kayıt URL\\'si')": "verbose_name=_('Recording URL')",
    "verbose_name=_('Paylaşılan Dosyalar')": "verbose_name=_('Shared Files')",
    "verbose_name=_('Şifreli mi?')": "verbose_name=_('Encrypted?')",
    "verbose_name=_('Bekleme Odası Aktif')": "verbose_name=_('Waiting Room Active')",
    "verbose_name = _('Telemedicine Konsültasyonu')": "verbose_name = _('Telemedicine Consultation')",
    "verbose_name_plural = _('Telemedicine Konsültasyonları')": "verbose_name_plural = _('Telemedicine Consultations')",
    
    # TeleMedicineMessage
    "verbose_name=_('Konsültasyon')": "verbose_name=_('Consultation')",
    "verbose_name=_('Gönderen')": "verbose_name=_('Sender')",
    "verbose_name=_('Mesaj Türü')": "verbose_name=_('Message Type')",
    "verbose_name=_('Dosya URL\\'si')": "verbose_name=_('File URL')",
    "verbose_name=_('Okundu mu?')": "verbose_name=_('Is Read?')",
    "verbose_name=_('Zaman')": "verbose_name=_('Time')",
    "verbose_name = _('Telemedicine Mesajı')": "verbose_name = _('Telemedicine Message')",
    "verbose_name_plural = _('Telemedicine Mesajları')": "verbose_name_plural = _('Telemedicine Messages')",
    
    # TeleMedicineSettings
    "verbose_name=_('Kullanıcı')": "verbose_name=_('User')",
    "verbose_name=_('Varsayılan Kamera Açık')": "verbose_name=_('Default Camera Enabled')",
    "verbose_name=_('Varsayılan Mikrofon Açık')": "verbose_name=_('Default Microphone Enabled')",
    "verbose_name=_('Video Kalitesi')": "verbose_name=_('Video Quality')",
    "verbose_name=_('Konsültasyon Hatırlatmaları')": "verbose_name=_('Consultation Reminders')",
    "verbose_name=_('Kaç Dakika Önce Hatırlat')": "verbose_name=_('Remind Minutes Before')",
    "verbose_name=_('E-posta Bildirimleri')": "verbose_name=_('Email Notifications')",
    "verbose_name=_('SMS Bildirimleri')": "verbose_name=_('SMS Notifications')",
    "verbose_name=_('Bekleme Odası Zorunlu')": "verbose_name=_('Waiting Room Required')",
    "verbose_name=_('Kayıt İzni')": "verbose_name=_('Recording Permission')",
}

# Apply replacements
for turkish, english in replacements.items():
    content = content.replace(turkish, english)

# Write back to file
with open('telemedicine/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Turkish verbose names fixed in telemedicine/models.py")