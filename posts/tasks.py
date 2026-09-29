from celery import shared_task
from channels.models import ChannelPost
from .post_handlers import post_handler


@shared_task
def publish_post_instantly(post_id):
    channel_posts = ChannelPost.objects.select_related(
        "workspace_channel", "post"
    ).filter(post=post_id)

    channel_post_list = list(channel_posts.all())

    for channel_post in channel_post_list:
        slug_url = channel_post.workspace_channel.channel.slug_url
        workspace_channel = channel_post.workspace_channel

        if not workspace_channel or not workspace_channel.is_active:
            channel_post.error_message = "Channel is deactivated or disconnected"
            channel_post.status = "failed"
            channel_post.save()
            return

        channel_config = workspace_channel.channel_config

        if not channel_config:
            channel_post.error_message = "Channel is disconnected"
            channel_post.status = "failed"
            channel_post.save()
            return
        
        config = channel_config.config
        
        if not config:
            channel_post.error_message = 'Channel is disconnected'
            channel_post.status = 'failed'
            channel_post.save()
            return

        print("channel_config", channel_config)

        handler = post_handler(slug_url=slug_url)

        handler.post_to_channel(
            channel_post=channel_post,
            post=channel_post.post,
            config=config,
            account_id = workspace_channel.account_id
        )
