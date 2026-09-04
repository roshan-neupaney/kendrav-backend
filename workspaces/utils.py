from django.utils.text import slugify
from django.utils.crypto import get_random_string

def generate_workspace_slug(title, workspace_id):
    slug_id = get_random_string(length=6)
    return slugify(f"{title}-{slug_id}-{workspace_id}")