from celery import shared_task
from posts.models import PostMedia
from datetime import datetime, timezone, timedelta
from django.conf import settings
import cloudinary.api


@shared_task
def cleanup_cloudinary_media():
    valid_time = datetime.now(timezone.utc) - timedelta(
        hours=settings.IMAGE_CLEAN_UP_INTERVAL
    )
    post_medias = PostMedia.objects.filter(is_active=False, updated_at__lte=valid_time)

    public_ids = []
    for media in list(post_medias):
        public_id = media.public_id
        if public_id:
            public_ids.append(public_id)

    if len(public_ids) > 0:
        result = cloudinary.api.delete_resources(public_ids)
        print(result)

        delete_images = result.get("deleted")

        post_media_to_delete = []
        if delete_images:
            for key, value in delete_images.items():
                if value == "deleted" or value == "not_found":
                    post_media_to_delete.append(key)

        post_medias.filter(public_id__in=post_media_to_delete).delete()
