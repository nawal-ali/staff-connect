from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Only title and body are editable; the author and slug are set by the app."""

    class Meta:
        model = Post
        fields = ("title", "body")
        widgets = {"body": forms.Textarea(attrs={"rows": 8})}
