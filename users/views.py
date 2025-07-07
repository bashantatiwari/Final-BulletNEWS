from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import SignupForm

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    return render(request, 'users/signup.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    return render(request, 'users/register.html', {'form': form})

def home_view(request):
    return render(request, 'users/home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'users/login.html')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Get the next URL from the request, or default to home
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, 'users/login.html')
            
    # For GET requests, store the next parameter in the template context
    next_url = request.GET.get('next')
    return render(request, 'users/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('core:home')

def failure(request):
    messages.error(request, "Authentication failed. Please try again.")
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def settings_view(request):
    if request.method == 'POST':
        print("POST request received")  # Debug message
        
        # Update user fields
        request.user.full_name = request.POST.get('full_name')
        request.user.email = request.POST.get('email')
        request.user.country = request.POST.get('country')
        request.user.gender = request.POST.get('gender')
        request.user.save()
        print("User fields updated")  # Debug message

        # Handle password update
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        print(f"Current password provided: {bool(current_password)}")  # Debug message
        print(f"New password provided: {bool(new_password)}")  # Debug message
        print(f"Confirm password provided: {bool(confirm_password)}")  # Debug message
        
        if current_password and new_password and confirm_password:
            print("All password fields are filled")  # Debug message
            print(f"Username: {request.user.username}")  # Debug message
            
            # Try to authenticate the user with the current password
            user = authenticate(request, username=request.user.username, password=current_password)
            if user is None:
                print("Current password is incorrect")  # Debug message
                messages.error(request, "Current password is incorrect.")
                return render(request, 'users/settings.html', {'user': request.user})
            
            if new_password != confirm_password:
                print("New passwords do not match")  # Debug message
                messages.error(request, "New passwords do not match.")
                return render(request, 'users/settings.html', {'user': request.user})
            
            try:
                request.user.set_password(new_password)
                request.user.save()
                print("Password updated successfully")  # Debug message
                messages.success(request, "Password updated successfully.")
                return redirect('users:settings')
            except Exception as e:
                print(f"Error updating password: {str(e)}")  # Debug message
                messages.error(request, "Error updating password. Please try again.")
                return render(request, 'users/settings.html', {'user': request.user})
        else:
            print("Not all password fields are filled")  # Debug message
    
    return render(request, 'users/settings.html', {'user': request.user})

def social_auth(request):
    # Placeholder for social authentication logic
    return redirect('users:home')
