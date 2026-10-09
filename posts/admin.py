from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "body", "author__username")
    list_filter = ("created_at", "author")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    fieldsets = (
        ("Content", {"fields": ("title", "slug", "body")}),
        ("Publishing", {"fields": ("author",)}),
    )
