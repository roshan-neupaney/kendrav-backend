from celery import shared_task
from posts.models import PostMedia
from datetime import datetime, timezone, timedelta
from django.conf import settings
import cloudinary.api

@shared_task
def cleanup_cloudinary_media():
    valid_time = datetime.now(timezone.utc) - timedelta(hours=settings.IMAGE_CLEAN_UP_INTERVAL)
    # post_medias = PostMedia.objects.filter(is_active=False, updated_at__lte = valid_time)

    public_ids = ['post/Screenshot from 2026-10-02 11-14-12.png', 'post/Screenshot from 2026-10-02 11-14-12.png_1790944733']
    # for media in post_medias:
    #     public_id = media.media_url.public_id
    cloudinary.api.delete_resources(public_ids)