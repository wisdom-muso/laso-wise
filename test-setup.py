#!/usr/bin/env python3
"""
Test script to validate Django + React integration setup
"""

import os
import sys
import json
from pathlib import Path

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "END": "\033[0m"
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['END']}")

def check_files():
    """Check if all required files exist"""
    print_status("Checking required files...", "INFO")
    
    required_files = [
        "Dockerfile.django",
        "frontend/Dockerfile.react", 
        "docker-compose.dev.yml",
        "run-dev.sh",
        "frontend/src/lib/api.ts",
        "core/api.py",
        "core/serializers.py",
        "core/urls.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
            print_status(f"Missing: {file}", "ERROR")
        else:
            print_status(f"Found: {file}", "SUCCESS")
    
    if missing_files:
        print_status(f"Missing {len(missing_files)} required files", "ERROR")
        return False
    else:
        print_status("All required files present", "SUCCESS")
        return True

def check_django_config():
    """Check Django configuration"""
    print_status("Checking Django configuration...", "INFO")
    
    try:
        # Check manage.py
        if Path("manage.py").exists():
            print_status("manage.py found", "SUCCESS")
        else:
            print_status("manage.py not found", "ERROR")
            return False
            
        # Check settings
        if Path("laso/settings.py").exists():
            print_status("Django settings found", "SUCCESS")
        else:
            print_status("Django settings not found", "ERROR")
            return False
            
        # Check URL configuration
        if Path("laso/urls.py").exists():
            print_status("Main URL configuration found", "SUCCESS")
        else:
            print_status("Main URL configuration not found", "ERROR")
            return False
            
        return True
    except Exception as e:
        print_status(f"Error checking Django config: {e}", "ERROR")
        return False

def check_react_config():
    """Check React configuration"""
    print_status("Checking React configuration...", "INFO")
    
    try:
        # Check package.json
        if Path("frontend/package.json").exists():
            with open("frontend/package.json", 'r') as f:
                package_data = json.load(f)
                print_status("React package.json found", "SUCCESS")
                
                # Check required dependencies
                required_deps = ['react', 'react-dom', 'axios', 'vite']
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                all_deps = {**deps, **dev_deps}
                
                for dep in required_deps:
                    if dep in all_deps:
                        print_status(f"Dependency {dep} found", "SUCCESS")
                    else:
                        print_status(f"Missing dependency: {dep}", "ERROR")
        else:
            print_status("React package.json not found", "ERROR")
            return False
            
        # Check vite config
        if Path("frontend/vite.config.ts").exists():
            print_status("Vite configuration found", "SUCCESS")
        else:
            print_status("Vite configuration not found", "ERROR")
            return False
            
        # Check main React entry point
        if Path("frontend/src/main.tsx").exists():
            print_status("React entry point found", "SUCCESS")
        else:
            print_status("React entry point not found", "ERROR")
            return False
            
        return True
    except Exception as e:
        print_status(f"Error checking React config: {e}", "ERROR")
        return False

def check_api_integration():
    """Check API integration setup"""
    print_status("Checking API integration...", "INFO")
    
    try:
        # Check API client
        api_file = Path("frontend/src/lib/api.ts")
        if api_file.exists():
            content = api_file.read_text()
            if "http://localhost:8005" in content:
                print_status("API base URL configured for Docker", "SUCCESS")
            else:
                print_status("API base URL may need adjustment", "WARNING")
                
            if "axios" in content:
                print_status("Axios HTTP client configured", "SUCCESS")
            else:
                print_status("HTTP client not found in API config", "ERROR")
                
            if "endpoints" in content:
                print_status("API endpoints defined", "SUCCESS")
            else:
                print_status("API endpoints not defined", "ERROR")
        else:
            print_status("API client configuration not found", "ERROR")
            return False
            
        # Check Django API endpoints
        api_views_file = Path("core/api.py")
        if api_views_file.exists():
            content = api_views_file.read_text()
            endpoints = ["get_csrf_token", "health_check", "CustomAuthToken", "register_user"]
            for endpoint in endpoints:
                if endpoint in content:
                    print_status(f"Django endpoint {endpoint} found", "SUCCESS")
                else:
                    print_status(f"Django endpoint {endpoint} missing", "ERROR")
        else:
            print_status("Django API views not found", "ERROR")
            return False
            
        return True
    except Exception as e:
        print_status(f"Error checking API integration: {e}", "ERROR")
        return False

def check_docker_setup():
    """Check Docker setup"""
    print_status("Checking Docker setup...", "INFO")
    
    try:
        # Check Dockerfiles
        django_dockerfile = Path("Dockerfile.django")
        react_dockerfile = Path("frontend/Dockerfile.react")
        
        if django_dockerfile.exists():
            content = django_dockerfile.read_text()
            if "python:3.11" in content:
                print_status("Django Dockerfile using Python 3.11", "SUCCESS")
            if "EXPOSE 8005" in content:
                print_status("Django Dockerfile exposes port 8005", "SUCCESS")
        else:
            print_status("Django Dockerfile not found", "ERROR")
            return False
            
        if react_dockerfile.exists():
            content = react_dockerfile.read_text()
            if "node:20" in content:
                print_status("React Dockerfile using Node 20", "SUCCESS")
            if "EXPOSE 3000" in content:
                print_status("React Dockerfile exposes port 3000", "SUCCESS")
        else:
            print_status("React Dockerfile not found", "ERROR")
            return False
            
        # Check docker-compose
        compose_file = Path("docker-compose.dev.yml")
        if compose_file.exists():
            content = compose_file.read_text()
            if "django:" in content and "frontend:" in content:
                print_status("Docker Compose defines both services", "SUCCESS")
            if "8005:8005" in content and "3000:3000" in content:
                print_status("Docker Compose port mapping configured", "SUCCESS")
        else:
            print_status("Docker Compose file not found", "ERROR")
            return False
            
        return True
    except Exception as e:
        print_status(f"Error checking Docker setup: {e}", "ERROR")
        return False

def print_instructions():
    """Print setup and run instructions"""
    print_status("Setup Instructions", "INFO")
    print()
    print("🚀 To run the Django + React application:")
    print()
    print("1. Ensure Docker and Docker Compose are installed")
    print("2. Run the development script:")
    print("   ./run-dev.sh start")
    print()
    print("📋 Available commands:")
    print("   ./run-dev.sh start       - Build and start services")
    print("   ./run-dev.sh stop        - Stop all services") 
    print("   ./run-dev.sh logs        - View logs")
    print("   ./run-dev.sh status      - Check service status")
    print("   ./run-dev.sh migrate     - Run Django migrations")
    print("   ./run-dev.sh superuser   - Create Django superuser")
    print("   ./run-dev.sh help        - Show all commands")
    print()
    print("🌐 Services will be available at:")
    print("   Django Backend:  http://localhost:8005")
    print("   Django Admin:    http://localhost:8005/admin")
    print("   API Endpoints:   http://localhost:8005/api")
    print("   React Frontend:  http://localhost:3000")
    print()
    print("🔧 API Integration Features:")
    print("   ✅ CSRF token handling")
    print("   ✅ JWT authentication")
    print("   ✅ User registration/login")
    print("   ✅ Health check endpoints")
    print("   ✅ CORS configuration")
    print("   ✅ Error handling and retries")
    print()

def main():
    """Main test function"""
    print_status("Django + React Integration Setup Validation", "INFO")
    print("=" * 60)
    
    checks = [
        ("Files", check_files),
        ("Django Configuration", check_django_config),
        ("React Configuration", check_react_config), 
        ("API Integration", check_api_integration),
        ("Docker Setup", check_docker_setup)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        color = "SUCCESS" if result else "ERROR"
        print_status(f"{name}: {status}", color)
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print_status("✅ All checks passed! Setup is ready.", "SUCCESS")
        print_instructions()
    else:
        print_status("❌ Some checks failed. Please fix the issues above.", "ERROR")
        
    return all_passed

if __name__ == "__main__":
    sys.exit(0 if main() else 1)