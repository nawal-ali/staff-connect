from django.utils.text import slugify


def generate_unique_slug(model, value, max_length=50):
    """Build a slug from `value` that is not used yet by `model`."""
    base = slugify(value)[:max_length] or "post"
    slug = base
    counter = 2
    while model.objects.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
        counter += 1
    return slug
