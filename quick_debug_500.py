#!/usr/bin/env python3
"""
Quick debug script to identify potential 500 error causes
"""

import os
import sys

def check_potential_issues():
    """Check for common issues that cause 500 errors"""
    
    print("🔍 Quick 500 Error Debug Check")
    print("=" * 40)
    
    issues_found = []
    
    # Check if required files exist
    required_files = [
        'meditrack/settings.py',
        'meditrack/urls.py', 
        'meditrack/wsgi.py',
        'core/views_auth.py',
        'core/forms.py',
        'Templates/core/login.html',
        'manage.py'
    ]
    
    print("📁 Checking required files...")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING!")
            issues_found.append(f"Missing file: {file_path}")
    
    # Check for common syntax errors in key files
    print("\n🐍 Checking Python syntax...")
    key_python_files = [
        'meditrack/settings.py',
        'core/views_auth.py',
        'core/forms.py',
        'manage.py'
    ]
    
    for file_path in key_python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"   ✅ {file_path}")
            except SyntaxError as e:
                print(f"   ❌ {file_path} - SYNTAX ERROR: {e}")
                issues_found.append(f"Syntax error in {file_path}: {e}")
            except Exception as e:
                print(f"   ⚠️  {file_path} - Could not check: {e}")
    
    # Check for missing imports
    print("\n📦 Checking critical imports...")
    try:
        sys.path.insert(0, '.')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meditrack.settings')
        
        import django
        django.setup()
        
        # Try importing key components
        from django.conf import settings
        print("   ✅ Django settings imported")
        
        from core.views_auth import CustomLoginView
        print("   ✅ Login view imported")
        
        from core.forms import LoginForm  
        print("   ✅ Login form imported")
        
        from django.urls import reverse
        login_url = reverse('login')
        print(f"   ✅ Login URL resolves: {login_url}")
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        issues_found.append(f"Import error: {e}")
    
    # Check environment variables
    print("\n🌍 Checking environment...")
    env_vars_to_check = [
        'SECRET_KEY',
        'DEBUG', 
        'ALLOWED_HOSTS'
    ]
    
    for var in env_vars_to_check:
        value = os.getenv(var, 'NOT SET')
        if value == 'NOT SET':
            print(f"   ⚠️  {var}: {value}")
        else:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
    
    print("\n📋 SUMMARY")
    print("-" * 20)
    
    if issues_found:
        print("❌ Issues found:")
        for issue in issues_found:
            print(f"   • {issue}")
        print("\n💡 These issues may be causing the 500 error.")
    else:
        print("✅ No obvious issues found in quick check.")
        print("\n💡 500 error may be caused by:")
        print("   • Database connection issues")
        print("   • Missing migrations")
        print("   • Runtime errors in views")
        print("   • Static file serving problems")
    
    print("\n🔧 Next steps:")
    print("   1. Run: ./fix_500_error.sh")
    print("   2. Check Docker logs: docker logs laso_web")
    print("   3. Run Django checks inside container:")
    print("      docker exec laso_web python manage.py check")

if __name__ == "__main__":
    check_potential_issues()