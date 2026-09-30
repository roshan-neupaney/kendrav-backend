from channels.models import WorkspaceChannel, ChannelConfig
import requests
from posts.models import PostMedia
from datetime import datetime, timezone


def post_handler(slug_url):
    handlers = {"facebook": FacebookHandler}
    return handlers.get(slug_url)()


class FacebookHandler:
    def post_to_channel(self, channel_post, post, config, account_id):

        payload = {}

        access_token = config.get("page_access_token", None)
        if access_token:
            payload["access_token"] = access_token

        post_medias = PostMedia.objects.filter(post=post.id).order_by("order")

        post_medias_list = list(post_medias.all())

        media_res_ids = []
        if post_medias_list and len(post_medias_list) > 0:
            for media in post_medias_list:
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

                            media_res_ids.append({"media_fbid": media_json.get("id")})
                            break

                except Exception as e:
                    print(e)

        if post.caption:
            payload["message"] = post.caption
        if post.link:
            payload["link"] = post.link

        payload["attached_media"] = media_res_ids

        error_message = ''
        for i in range(4):
            response = requests.post(
                f"https://graph.facebook.com/v26.0/{account_id}/feed", json=payload
            )
            if response.ok:
                res_json = response.json()
                channel_post.status = 'published'
                channel_post.published_at = datetime.now(timezone.utc)
                channel_post.platform_post_id = res_json.get('id')
                error_message = ''
                channel_post.save()
                return

            error_message = response.text
        
        channel_post.status = 'process_failed'
        channel_post.error_message = error_message
        
        channel_post.save()