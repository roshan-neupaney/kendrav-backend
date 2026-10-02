from celery import shared_task
from posts.models import PostMedia
from datetime import datetime, timezone, timedelta
from django.conf import settings
import cloudinary.api

@shared_task
def cleanup_cloudinary_media():
    valid_time = datetime.now(timezone.utc) - timedelta(seconds=settings.IMAGE_CLEAN_UP_INTERVAL)
    post_medias = PostMedia.objects.filter(is_active=False, updated_at__lte=valid_time)

    public_ids = []
    for media in post_medias:
        public_id = media.public_id
        if public_id:
            public_ids.append(public_id)

    if len(public_ids) > 0:
        result = cloudinary.api.delete_resources(public_ids)
        print(result)
    