from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    """Custom view that logs out the user and redirects to login page."""
    logout(request)
    return redirect('login')
