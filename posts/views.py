from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import PostForm
from .mixins import AuthorRequiredMixin
from .models import Post


class PostListView(ListView):
    """Home page: paginated list of all announcements."""

    model = Post
    template_name = "home.html"
    context_object_name = "posts"
    paginate_by = settings.POSTS_PER_PAGE

    def get_queryset(self):
        return Post.objects.select_related("author", "author__profile")


class PostDetailView(DetailView):
    """A single announcement, looked up by its slug."""

    model = Post
    context_object_name = "post"


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Announcement published.")
        return response


class PostUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Announcement updated.")
        return response


class PostDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("home")
    http_method_names = ["post"]  # delete is POST-only: GET is not accepted

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Announcement deleted.")
        return response
