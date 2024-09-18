# users/decorators.py
from django.shortcuts import redirect

def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:main_page')  # Redirect to the home page or any other page
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func