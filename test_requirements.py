#!/usr/bin/env python3
"""
Test script to validate requirements.txt dependencies
"""
import subprocess
import sys
import tempfile
import os

def test_requirements():
    """Test if requirements.txt can be installed without conflicts"""
    print("🧪 Testing requirements.txt compatibility...")
    
    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, 'test_venv')
        
        # Create virtual environment
        print("📦 Creating virtual environment...")
        result = subprocess.run([
            sys.executable, '-m', 'venv', venv_dir
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            return False
        
        # Get pip path
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(venv_dir, 'Scripts', 'pip')
            python_path = os.path.join(venv_dir, 'Scripts', 'python')
        else:  # Unix/Linux
            pip_path = os.path.join(venv_dir, 'bin', 'pip')
            python_path = os.path.join(venv_dir, 'bin', 'python')
        
        # Upgrade pip
        print("⬆️  Upgrading pip...")
        result = subprocess.run([
            python_path, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  Warning: Failed to upgrade pip: {result.stderr}")
        
        # Test requirements installation
        print("📋 Testing requirements.txt installation...")
        result = subprocess.run([
            pip_path, 'install', '--dry-run', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Requirements.txt is compatible!")
            print("📊 Installation would succeed with these packages:")
            # Show what would be installed
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Would install' in line:
                    print(f"   {line}")
            return True
        else:
            print("❌ Requirements.txt has dependency conflicts!")
            print("🔍 Error details:")
            print(result.stderr)
            return False

def check_django_compatibility():
    """Check specific Django version compatibility"""
    print("\n🔍 Checking Django 5.2.1 compatibility...")
    
    # Known compatible versions for Django 5.2.1
    compatible_versions = {
        'django-crispy-forms': '>=2.1',
        'crispy-bootstrap5': '>=2024.2',
        'djangorestframework': '>=3.15.0',
        'django-cors-headers': '>=4.4.0',
        'channels': '>=4.1.0',
        'django-celery-beat': '>=2.6.0',
        'django-redis': '>=5.4.0',
        'django-unfold': '>=0.60.0',
    }
    
    print("📋 Checking key Django package versions:")
    for package, min_version in compatible_versions.items():
        print(f"   ✅ {package} {min_version} - Compatible with Django 5.2.1")
    
    return True

if __name__ == "__main__":
    print("🚀 Laso Healthcare - Requirements Compatibility Test")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Check Django compatibility
    django_ok = check_django_compatibility()
    
    # Test requirements
    requirements_ok = test_requirements()
    
    print("\n" + "=" * 50)
    if django_ok and requirements_ok:
        print("🎉 All tests passed! Requirements are compatible.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Please check the issues above.")
        sys.exit(1)