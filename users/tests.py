import io
import re
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Profile

PASSWORD = "Str0ng-pass-123"


def make_image(name="avatar.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "blue").save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class RegistrationTests(TestCase):
    def register(self, **overrides):
        data = {
            "username": "sara",
            "email": "sara@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return self.client.post(reverse("register"), data)

    def test_register_creates_user_hashed_password_and_profile(self):
        response = self.register()
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="sara")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_rejects_mismatched_passwords(self):
        response = self.register(password2="something-else-123")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sara").exists())

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user("other", "sara@example.com", PASSWORD)
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sara").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sara", "sara@example.com", PASSWORD)

    def test_login_success_redirects(self):
        response = self.client.post(
            reverse("login"), {"username": "sara", "password": PASSWORD}
        )
        self.assertRedirects(
            response, reverse(settings.LOGIN_REDIRECT_URL), fetch_redirect_response=False
        )

    def test_login_wrong_password_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "sara", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")

    def test_login_honours_safe_next_url(self):
        response = self.client.post(
            reverse("login") + "?next=/announcements/new/",
            {"username": "sara", "password": PASSWORD},
        )
        self.assertRedirects(response, "/announcements/new/", fetch_redirect_response=False)

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            reverse("login") + "?next=https://evil.example.com/",
            {"username": "sara", "password": PASSWORD},
        )
        self.assertRedirects(
            response, reverse(settings.LOGIN_REDIRECT_URL), fetch_redirect_response=False
        )

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

    def test_logout_post_logs_out(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordResetTests(TestCase):
    def test_full_reset_flow(self):
        user = User.objects.create_user("sara", "sara@example.com", "Old-pass-12345")
        response = self.client.post(reverse("password_reset"), {"email": "sara@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        link = re.search(r"http://testserver(/users/reset/\S+)", mail.outbox[0].body).group(1)
        response = self.client.get(link, follow=True)
        set_password_url = response.redirect_chain[-1][0]
        response = self.client.post(
            set_password_url,
            {"new_password1": "New-pass-98765", "new_password2": "New-pass-98765"},
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("New-pass-98765"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sara", "sara@example.com", PASSWORD)
        self.client.force_login(self.user)

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('profile')}", fetch_redirect_response=False
        )

    def test_profile_shows_default_avatar_when_none_uploaded(self):
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "img/default-avatar.svg")

    def test_edit_profile_saves_data_and_avatar(self):
        response = self.client.post(
            reverse("edit_profile"),
            {
                "display_name": "Sara M.",
                "department": "HR",
                "bio": "Hello!",
                "avatar": make_image(),
            },
        )
        self.assertRedirects(response, reverse("profile"))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "Sara M.")
        self.assertEqual(profile.department, "HR")
        self.assertTrue(profile.avatar.name.startswith("avatars/"))

    def test_edit_profile_rejects_executable_file(self):
        response = self.client.post(
            reverse("edit_profile"),
            {"display_name": "Sara", "department": "HR", "avatar": make_image("evil.exe")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("avatar"))
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_edit_profile_rejects_extension_not_in_allowed_list(self):
        # .bmp is a real image type, but our own validator only allows jpg/png/gif/webp
        response = self.client.post(
            reverse("edit_profile"),
            {"display_name": "Sara", "department": "HR", "avatar": make_image("photo.bmp")},
        )
        self.assertContains(response, "Unsupported file type")
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    @override_settings(AVATAR_MAX_SIZE=10)
    def test_edit_profile_rejects_large_file(self):
        response = self.client.post(
            reverse("edit_profile"),
            {"display_name": "Sara", "department": "HR", "avatar": make_image()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "too large")

    def test_edit_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 302)

    def test_user_can_only_edit_own_profile(self):
        other = User.objects.create_user("omar", "omar@example.com", PASSWORD)
        self.client.post(
            reverse("edit_profile"), {"display_name": "Changed", "department": "IT"}
        )
        self.assertEqual(Profile.objects.get(user=other).display_name, "")
        self.assertEqual(Profile.objects.get(user=self.user).display_name, "Changed")
