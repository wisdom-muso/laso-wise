#!/usr/bin/env python3
"""
Static Files Fix Script for LASO Healthcare
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meditrack.settings')

try:
    django.setup()
    
    from django.conf import settings
    from django.core.management import execute_from_command_line
    
    print("🔧 LASO Healthcare - Static Files Fix")
    print("=" * 40)
    
    print(f"📁 STATIC_URL: {settings.STATIC_URL}")
    print(f"📁 STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"📁 STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    # Check if static files exist
    static_dirs = settings.STATICFILES_DIRS
    for static_dir in static_dirs:
        css_dir = os.path.join(static_dir, 'assets', 'css')
        if os.path.exists(css_dir):
            print(f"✅ Static CSS directory found: {css_dir}")
            css_files = [f for f in os.listdir(css_dir) if f.endswith('.css')]
            print(f"   CSS files: {css_files}")
        else:
            print(f"❌ Static CSS directory not found: {css_dir}")
    
    # Check if collectstatic is needed
    static_root = settings.STATIC_ROOT
    if not os.path.exists(static_root):
        print(f"📦 Creating STATIC_ROOT directory: {static_root}")
        os.makedirs(static_root, exist_ok=True)
    
    print("\n🔄 Running collectstatic...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
    
    # Verify collected files
    collected_css = os.path.join(static_root, 'assets', 'css')
    if os.path.exists(collected_css):
        print(f"✅ CSS files collected to: {collected_css}")
        css_files = [f for f in os.listdir(collected_css) if f.endswith('.css')]
        print(f"   Collected CSS files: {css_files}")
    else:
        print(f"❌ CSS files not collected to: {collected_css}")
    
    print("\n✅ Static files fix completed!")
    print("\n📋 Next steps:")
    print("   1. Restart your Django server")
    print("   2. Check dashboard at: http://65.108.91.110:8000/dashboard/")
    print("   3. Verify teal colors are applied")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()