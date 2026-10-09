from django.contrib.auth.mixins import UserPassesTestMixin


class AuthorRequiredMixin(UserPassesTestMixin):
    """Only the author of the post may continue; everyone else gets a 403."""

    def test_func(self):
        return self.get_object().author == self.request.user
