# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CustomUserCreationForm
from django.contrib import messages
from .decorators import unauthenticated_user
from django.contrib.auth.decorators import login_required

def about(request):
    return render(request, 'about.html')

@unauthenticated_user
def landing_page(request):
    return render(request, 'landing_page.html')

@unauthenticated_user
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@unauthenticated_user
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {user.username}!")
                return redirect('users:main_page')  # Correct URL pattern name
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('landing_page')

@login_required
def main_page(request):
    return render(request, 'main.html')

def contact(request):
    return render(request, 'users/contact.html')