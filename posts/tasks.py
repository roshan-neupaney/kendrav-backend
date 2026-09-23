from celery import shared_task
from channels.models import ChannelPost
from .post_handlers import post_handler


@shared_task
def publish_post_to_channel(post_id):
    channel_posts = ChannelPost.objects.select_related("workspace_channel").filter(
        post=post_id, workspace_channel__is_active=True
    )

    channel_post_list = list(channel_posts.all())

    for post in channel_post_list:
        slug_url = post.workspace_channel.channel.slug_url
        workspace_channel_id = post.workspace_channel.id
        handler = post_handler(slug_url=slug_url)

        handler.post_to_channel(workspace_channel_id=workspace_channel_id)
