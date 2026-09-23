from channels.models import ChannelConfig


def post_handler(slug_url):
    handlers = {"facebook": FacebookHandler}
    return handlers.get(slug_url)()


class FacebookHandler:
    def post_to_channel(self, workspace_channel_id):
        channel_config = ChannelConfig.objects.filter(
            workspace_channel__is_active=True, workspace_channel=workspace_channel_id
        ).first()

        print('post to facebook using channel_config')
