import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, RegisterForm
from .models import Profile
from .utils import get_safe_next_url

logger = logging.getLogger(__name__)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created. You can now log in.")
            return redirect("login")
        messages.error(request, "Registration failed. Please fix the errors below.")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_username()}!")
            return redirect(get_safe_next_url(request))
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    next_url = request.POST.get("next") or request.GET.get("next", "")
    return render(request, "users/login.html", {"form": form, "next": next_url})


@require_POST  # GET requests receive "405 Method Not Allowed"
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "users/profile.html", {"profile": profile_obj})


@login_required
def edit_profile(request):
    # Always the logged-in user's own profile: nobody can edit someone else's.
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            try:
                form.save()
            except OSError:
                logger.exception("Could not save profile data for %s", request.user)
                messages.error(
                    request, "We could not save your changes. Please try again later."
                )
            else:
                messages.success(request, "Your profile has been updated.")
                return redirect("profile")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=profile_obj)

    return render(request, "users/edit_profile.html", {"form": form})
