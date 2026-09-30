from celery import shared_task
from channels.models import ChannelPost
from .post_handlers import post_handler
from .models import Post


@shared_task
def publish_post_instantly(post_id):
    channel_posts = ChannelPost.objects.select_related("workspace_channel").filter(
        post=post_id
    )
    post = Post.objects.filter(id=post_id).first()

    channel_post_list = list(channel_posts.all())

    for channel_post in channel_post_list:
        slug_url = channel_post.workspace_channel.channel.slug_url
        workspace_channel = channel_post.workspace_channel

        if not workspace_channel or not workspace_channel.is_active:
            channel_post.error_message = "Channel is deactivated or disconnected"
            channel_post.status = "failed"
            channel_post.save()
            continue

        channel_config = workspace_channel.channel_config

        if not channel_config:
            channel_post.error_message = "Channel is disconnected"
            channel_post.status = "failed"
            channel_post.save()
            continue

        config = channel_config.config

        if not config:
            channel_post.error_message = "Channel is disconnected"
            channel_post.status = "failed"
            channel_post.save()
            continue

        handler = post_handler(slug_url=slug_url)

        handler.post_to_channel(
            channel_post=channel_post,
            post=channel_post.post,
            config=config,
            account_id=workspace_channel.account_id,
        )

    published_count = sum(1 for cp in channel_post_list if cp.status == "published")
    failed_count = sum(1 for cp in channel_post_list if cp.status != "published")

    if published_count == 0:
        post.status = "failed"
    elif failed_count == 0:
        post.status = "published"
    else:
        post.status = "partial"

    post.save()

@shared_task
def post_to_each_channel(channel_post):
    return
