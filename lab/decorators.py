from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def lab_login_required(view_func):
    """Decorator that ensures the user is authenticated and is a lab worker."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the Lab Dashboard.')
            return redirect('lab-login')
        if not request.user.is_labworker:
            messages.error(request, 'You do not have permission to access the Lab Dashboard.')
            return redirect('lab-login')
        return view_func(request, *args, **kwargs)
    return wrapper
