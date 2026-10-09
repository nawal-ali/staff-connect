from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme


def get_display_name(user):
    """Return the profile display name, falling back to the username."""
    profile = getattr(user, "profile", None)
    if profile is not None and profile.display_name:
        return profile.display_name
    return user.get_username()


def get_safe_next_url(request, default=None):
    """Return the ?next= target only if it points to this site (no open redirect)."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return default or settings.LOGIN_REDIRECT_URL
