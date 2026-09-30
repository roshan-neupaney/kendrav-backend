from celery import shared_task
from channels.models import ChannelPost
from .post_handlers import post_handler
from .models import Post
from datetime import datetime, timezone
from channels.oauth_handlers import oauth_handler


@shared_task
def publish_post_instantly(post_id):
    channel_posts = ChannelPost.objects.filter(post=post_id)

    channel_post_list = list(channel_posts.all())

    for channel_post in channel_post_list:
        post_to_each_channel.delay(channel_post_id=channel_post.id, post_id=post_id)


@shared_task(bind=True, max_retries=3)
def post_to_each_channel(self, channel_post_id, post_id):
    channel_post = (
        ChannelPost.objects.select_related("workspace_channel")
        .filter(id=channel_post_id)
        .first()
    )
    workspace_channel = channel_post.workspace_channel
    slug_url = channel_post.workspace_channel.channel.slug_url

    if not workspace_channel or not workspace_channel.is_active:
        channel_post.error_message = "Channel is disconnected"
        channel_post.status = "failed"
        channel_post.save()
        mark_post_status.delay(post_id=post_id)
        return

    channel_config = workspace_channel.channel_config

    if not channel_config:
        channel_post.error_message = "Channel is disconnected"
        channel_post.status = "failed"
        channel_post.save()

        workspace_channel.is_active = False
        workspace_channel.save()
        mark_post_status.delay(post_id=post_id)
        return

    config = channel_config.config
    if not config:
        channel_post.error_message = "Channel is disconnected"
        channel_post.status = "failed"
        channel_post.save()

        workspace_channel.is_active = False
        workspace_channel.save()
        mark_post_status.delay(post_id=post_id)
        return

    auth_handler = oauth_handler(slug_url=slug_url)
    handler = post_handler(slug_url=slug_url)

    is_healthy = auth_handler.test_page(
        account_id=workspace_channel.account_id, config=config
    )

    if not is_healthy:
        channel_post.status = "failed"
        channel_post.error_message = "Channel is disconnected"
        channel_post.save()

        workspace_channel.is_active = False
        workspace_channel.save()
        mark_post_status.delay(post_id=post_id)
        return

    try:
        handler.post_to_channel(
            channel_post=channel_post,
            post=channel_post.post,
            config=config,
            account_id=workspace_channel.account_id,
        )

        mark_post_status.delay(post_id=post_id)

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            channel_post.status = "process_failed"
            channel_post.error_message = str(exc)
            channel_post.save()
            mark_post_status.delay(post_id=post_id)
            return
        raise self.retry(exc=exc, countdown=15)


@shared_task
def mark_post_status(post_id):
    post = Post.objects.prefetch_related("post_channels").filter(id=post_id).first()
    post_channels = post.post_channels.all()
    post_channels_list = list(post_channels)

    is_pending = post_channels.filter(status="pending").exists()

    failed_post = [cp for cp in post_channels if cp.status == "failed"]

    process_failed_post = [cp for cp in post_channels if cp.status == "process_failed"]

    is_some_failed = len(failed_post) > 0 and len(failed_post) != len(
        post_channels_list
    )
    is_some_process_failed = len(process_failed_post) > 0 and len(
        process_failed_post
    ) != len(post_channels_list)

    is_all_failed = len(failed_post) > 0 and len(failed_post) == len(post_channels_list)

    is_all_process_failed = len(process_failed_post) > 0 and len(
        process_failed_post
    ) == len(post_channels_list)

    if is_pending:
        post.status = "pending"

    if is_some_failed or is_some_process_failed:
        post.status = "partial"

    if is_all_failed:
        post.status = "failed"

    if is_all_process_failed:
        post.status = "process_failed"

    if not (
        is_pending
        or is_some_failed
        or is_some_process_failed
        or is_all_failed
        or is_all_process_failed
    ):
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)

    post.save()
