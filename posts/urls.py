from django.urls import path

from . import views

urlpatterns = [
    path("", views.PostListView.as_view(), name="home"),
    # "new" must come before the <slug> routes
    path("announcements/new/", views.PostCreateView.as_view(), name="post_create"),
    path("announcements/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("announcements/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("announcements/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
]
