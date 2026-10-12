import requests
from posts.models import PostMedia
from datetime import datetime, timezone
import json


def post_handler(slug_url):
    handlers = {"facebook": FacebookHandler}
    return handlers.get(slug_url)()


class FacebookHandler:
    def post_to_channel(self, channel_post, post, config, account_id):

        payload = {}

        access_token = config.get("page_access_token", None)
        if access_token:
            payload["access_token"] = access_token

        post_medias = PostMedia.objects.filter(post=post.id, is_active=True).order_by("order")

        post_medias_list = list(post_medias.all())

        media_res_ids = []
        if post_medias_list and len(post_medias_list) > 0:
            for media in post_medias_list:
                error = None
                media_upload_fail = False
                try:
                    for i in range(4):
                        media_response = requests.post(
                            f"https://graph.facebook.com/v26.0/{account_id}/photos",
                            json={
                                "url": media.media_url,
                                "published": False,
                                "access_token": access_token,
                            },
                        )
                        if media_response.ok:
                            media_json = media_response.json()

                            error = media_json.get("error", None)
                            id = media_json.get("id", None)
                            if not error and id:
                                media_res_ids.append({"media_fbid": id})
                                error = None
                                media_upload_fail = False
                                break
                            media_upload_fail = True

                        error = json.loads(media_response.text).get("error")["message"]

                except Exception as e:
                    media_upload_fail = True
                    print(e)

                if media_upload_fail:
                    raise Exception(f"Failed to upload image: {error}")
        
        if post.caption:
            payload["message"] = post.caption
        if post.link:
            payload["link"] = post.link

        payload["attached_media"] = media_res_ids

        error_message = ""

        response = requests.post(
            f"https://graph.facebook.com/v26.0/{account_id}/feed", json=payload
        )
        if response.ok:
            res_json = response.json()
            error = res_json.get("error", None)
            if error:
                error_message = error.get("message", "")
                channel_post.status = "process_failed"
                channel_post.error_message = error_message
                channel_post.save()
                return

            error_message = ""
            channel_post.status = "published"
            channel_post.published_at = datetime.now(timezone.utc)
            channel_post.platform_post_id = res_json.get("id")
            channel_post.error_message = ""
            channel_post.save()
            return

        error_message = response.text
        error_json = json.loads(error_message)

        channel_post.status = "process_failed"
        channel_post.error_message = error_json.get("error")["message"]

        channel_post.save()
