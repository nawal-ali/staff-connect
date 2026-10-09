from django.contrib.auth.models import User
from django.db import models
from django.templatetags.static import static

from .utils import get_display_name
from .validators import validate_avatar


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        validators=[validate_avatar],
    )

    def __str__(self):
        return self.user.username

    @property
    def name(self):
        return get_display_name(self.user)

    @property
    def avatar_url(self):
        """URL of the uploaded avatar, or the default placeholder image."""
        if self.avatar:
            return self.avatar.url
        return static("img/default-avatar.svg")
