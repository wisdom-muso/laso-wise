#!/usr/bin/env python3
"""
Simple script to verify the fixes made to the codebase
"""
import os
import re

def check_template_urls():
    """Check for fixed URLs in templates"""
    issues_found = []
    
    # Check doctor_list.html for appointment-create fixes
    doctor_list_path = "/workspace/Templates/core/doctor_list.html"
    if os.path.exists(doctor_list_path):
        with open(doctor_list_path, 'r') as f:
            content = f.read()
            
        # Check for namespaced appointment-create URLs
        if 'core:appointment-create' in content:
            print("✓ Fixed: doctor_list.html uses namespaced appointment-create URL")
        else:
            issues_found.append("doctor_list.html still has unnamespaced appointment-create URLs")
        
        # Check for English text
        turkish_patterns = ['Doktor', 'Randevu', 'Hastalar', 'Doktorlar']
        for pattern in turkish_patterns:
            if pattern in content:
                issues_found.append(f"doctor_list.html still contains Turkish text: {pattern}")
    
    # Check telemedicine URLs
    telemedicine_urls_path = "/workspace/telemedicine/urls.py"
    if os.path.exists(telemedicine_urls_path):
        with open(telemedicine_urls_path, 'r') as f:
            content = f.read()
            
        if "name='schedule'" in content:
            print("✓ Fixed: telemedicine URLs include schedule pattern")
        else:
            issues_found.append("telemedicine urls.py missing schedule URL pattern")
    
    # Check telemedicine views for CreateView
    telemedicine_views_path = "/workspace/telemedicine/views.py"
    if os.path.exists(telemedicine_views_path):
        with open(telemedicine_views_path, 'r') as f:
            content = f.read()
            
        if "TeleMedicineConsultationCreateView" in content:
            print("✓ Fixed: telemedicine views include CreateView")
        else:
            issues_found.append("telemedicine views.py missing TeleMedicineConsultationCreateView")
    
    return issues_found

def main():
    print("Checking fixes...")
    issues = check_template_urls()
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("\n✅ All fixes appear to be in place!")

if __name__ == "__main__":
    main()