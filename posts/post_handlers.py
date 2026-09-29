from channels.models import WorkspaceChannel, ChannelConfig
import requests
from posts.models import PostMedia


def post_handler(slug_url):
    handlers = {"facebook": FacebookHandler}
    return handlers.get(slug_url)()


class FacebookHandler:
    def post_to_channel(self, channel_post, post, config, account_id):

        payload = {}

        access_token = config.get("page_access_token", None)
        if access_token:
            payload["access_token"] = access_token
        
        post_medias = PostMedia.objects.filter(post=post.id)
        post_meidas_list = list(post_medias.all())
        # post_medias = post.post_medias
        print(post_meidas_list)

        media_res_ids = []
        if post_meidas_list and len(post_meidas_list) > 0:
            for media in post_meidas_list:
                try:
                    media_response = requests.post(
                        f"https://graph.facebook.com/v26.0/{account_id}/photos",
                        params={
                            "url": media.media_url,
                            "published": False,
                            "access_token": access_token,
                        },
                    )
                    print(media_response)
                    # media_res_ids.append({"media_fbid": media_response.id})
                except Exception as e:
                    print(e)

        # if post.caption:
        #     payload["message"] = post.caption
        # if post.link:
        #     payload["link"] = post.link

        # for i, media in enumerate(media_res_ids):
        #     payload[f"attached_media[{i}]"] = media

        # response = requests.post(
        #     f"https://graph.facebook.com/{account_id}/feed", json=payload
        # )

        # print(response)
