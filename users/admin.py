from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "department")
    search_fields = ("user__username", "user__email", "display_name", "department")
    list_filter = ("department",)
    fieldsets = (
        ("Account", {"fields": ("user",)}),
        ("Profile details", {"fields": ("display_name", "department", "bio", "avatar")}),
    )
