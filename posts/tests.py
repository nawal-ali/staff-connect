from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post

PASSWORD = "Str0ng-pass-123"


class PostTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user("alice", "alice@example.com", PASSWORD)
        cls.bob = User.objects.create_user("bob", "bob@example.com", PASSWORD)

    def make_post(self, title="Hello world", author=None, body="Some text"):
        return Post.objects.create(title=title, body=body, author=author or self.alice)


class SlugTests(PostTestCase):
    def test_slug_is_generated_from_title(self):
        self.assertEqual(self.make_post("My first post").slug, "my-first-post")

    def test_duplicate_titles_get_unique_slugs(self):
        first = self.make_post("Same title")
        second = self.make_post("Same title")
        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-2")

    def test_non_latin_title_still_gets_a_slug(self):
        self.assertEqual(self.make_post("إعلان مهم").slug, "post")


class ListAndDetailTests(PostTestCase):
    def test_home_is_paginated(self):
        for i in range(7):
            self.make_post(f"Post {i}")
        page_1 = self.client.get(reverse("home"))
        page_2 = self.client.get(reverse("home") + "?page=2")
        self.assertEqual(len(page_1.context["posts"]), 5)
        self.assertEqual(len(page_2.context["posts"]), 2)

    def test_home_shows_author_and_date(self):
        self.make_post("Hello world")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Hello world")
        self.assertContains(response, "alice")

    def test_detail_found_by_slug(self):
        post = self.make_post("Detail test")
        response = self.client.get(reverse("post_detail", kwargs={"slug": post.slug}))
        self.assertContains(response, "Detail test")

    def test_unknown_slug_returns_custom_404(self):
        response = self.client.get(reverse("post_detail", kwargs={"slug": "nope"}))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)

    def test_edit_delete_buttons_only_for_author(self):
        post = self.make_post()
        url = reverse("post_detail", kwargs={"slug": post.slug})

        self.client.force_login(self.alice)
        self.assertContains(self.client.get(url), "Delete")

        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(url), "Delete")

        self.client.logout()
        self.assertNotContains(self.client.get(url), "Delete")


class CreateTests(PostTestCase):
    def test_create_requires_login(self):
        response = self.client.get(reverse("post_create"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('post_create')}",
            fetch_redirect_response=False,
        )

    def test_create_sets_author_and_slug(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse("post_create"), {"title": "My first post", "body": "Welcome!"}
        )
        post = Post.objects.get(slug="my-first-post")
        self.assertEqual(post.author, self.alice)
        self.assertRedirects(response, post.get_absolute_url())


class OwnershipTests(PostTestCase):
    def setUp(self):
        self.post = self.make_post()
        self.update_url = reverse("post_update", kwargs={"slug": self.post.slug})
        self.delete_url = reverse("post_delete", kwargs={"slug": self.post.slug})

    def test_author_can_update(self):
        self.client.force_login(self.alice)
        self.client.post(self.update_url, {"title": "Changed", "body": "New body"})
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Changed")

    def test_other_user_cannot_update(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)
        self.assertEqual(
            self.client.post(self.update_url, {"title": "Hacked", "body": "x"}).status_code, 403
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Hello world")

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_does_not_accept_get(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(self.delete_url).status_code, 405)

    def test_author_can_delete_with_post(self):
        self.client.force_login(self.alice)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
