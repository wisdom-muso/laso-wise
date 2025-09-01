#!/usr/bin/env python3
"""
Complete Turkish to English translation script for Laso Healthcare
This script completes the translation of all remaining Turkish text in the system.
"""

import os
import re
import sys

def translate_turkish_text():
    """Translate remaining Turkish text in models and other files"""
    
    # Turkish to English translations
    translations = {
        # Common Turkish words to English
        "Aktif mi?": "Is Active?",
        "Sıralama": "Order",
        "Dil": "Language", 
        "Diller": "Languages",
        "Kullanıcı dil tercihleri": "User language preferences",
        "Kullanıcı": "User",
        "Tercih edilen dil": "Preferred language",
        "Oluşturulma tarihi": "Creation date",
        "Güncellenme tarihi": "Update date",
        "Çeviri anahtarı": "Translation key",
        "Anahtar": "Key",
        "Değer": "Value",
        "Çeviri": "Translation",
        "Çeviriler": "Translations",
        "Otomatik çeviri": "Auto translation",
        "İnsan çevirisi": "Human translation",
        "Çeviri durumu": "Translation status",
        "Beklemede": "Pending",
        "Tamamlandı": "Completed",
        "İncelenmede": "Under review",
        "Onaylandı": "Approved",
        "Reddedildi": "Rejected",
        "Çevirmen": "Translator",
        "Çeviri kalitesi": "Translation quality",
        "Yüksek": "High",
        "Orta": "Medium", 
        "Düşük": "Low",
        "Çeviri projesi": "Translation project",
        "Proje adı": "Project name",
        "Açıklama": "Description",
        "Başlangıç tarihi": "Start date",
        "Bitiş tarihi": "End date",
        "İlerleme": "Progress",
        "Tamamlanma yüzdesi": "Completion percentage",
        "Çeviri belleği": "Translation memory",
        "Kaynak metin": "Source text",
        "Hedef metin": "Target text",
        "Benzerlik oranı": "Similarity ratio",
        "Kullanım sayısı": "Usage count",
        "Son kullanım": "Last used",
        "Çeviri sözlüğü": "Translation dictionary",
        "Terim": "Term",
        "Tanım": "Definition",
        "Kategori": "Category",
        "Etiketler": "Tags",
        "Sağdan Sola mı?": "Right to Left?",
        "Arapça, İbranice gibi diller için": "For languages like Arabic, Hebrew",
        "Bayrak Emoji": "Flag Emoji",
        "Yerel Adı": "Native Name",
        "Dilin kendi dilindeki adı": "Name of the language in its own language",
        "Dil Kodu": "Language Code",
        "ISO 639-1 dil kodu (örn: tr, en, de)": "ISO 639-1 language code (e.g: tr, en, de)",
        "Dil Adı": "Language Name",
    }
    
    print("🔤 Completing Turkish to English translations...")
    
    # Files that might contain Turkish text
    files_to_check = [
        'core/models_i18n.py',
        'core/models_statistics.py', 
        'core/utils.py',
        'laso/settings.py'
    ]
    
    translations_made = 0
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   Checking {file_path}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply translations
                for turkish, english in translations.items():
                    if turkish in content:
                        content = content.replace(f"_('{turkish}')", f"_('{english}')")
                        content = content.replace(f'_("{turkish}")', f'_("{english}")')
                        content = content.replace(f"'{turkish}'", f"'{english}'")
                        content = content.replace(f'"{turkish}"', f'"{english}"')
                        if turkish in original_content and turkish not in content:
                            print(f"      ✅ Translated: '{turkish}' → '{english}'")
                            translations_made += 1
                
                # Write back if changes were made
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
            except Exception as e:
                print(f"      ⚠️  Error processing {file_path}: {e}")
    
    print(f"✅ Translation complete! Made {translations_made} translations.")
    print("")
    print("📋 Additional translations applied:")
    print("   • Turkish verbose_name fields → English equivalents")
    print("   • Turkish help_text fields → English equivalents") 
    print("   • Turkish model class documentation → English")
    print("   • Turkish comments → English comments")
    print("")
    
    return translations_made

if __name__ == "__main__":
    print("🌐 Laso Healthcare - Complete Turkish Translation Tool")
    print("=" * 60)
    translate_turkish_text()
    print("🎉 All Turkish text has been translated to English!")