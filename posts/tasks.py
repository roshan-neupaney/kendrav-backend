from celery import shared_task
from channels.models import ChannelPost
from .post_handlers import post_handler
from .models import Post
from datetime import datetime, timezone
from channels.oauth_handlers import oauth_handler
from notifications.tasks import send_notification
from notifications.models import Notification, UserNotification
from django.conf import settings
from workspaces.models import WorkspaceMember


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
    post = Post.objects.prefetch_related("channel_posts").select_related('workspace').filter(id=post_id).first()
    channel_posts = post.channel_posts.all()
    channel_posts_list = list(channel_posts)

    workspace = post.workspace

    status_found = False
    
    is_pending = is_some_failed = is_some_process_failed = is_all_failed = is_all_process_failed = False

    is_pending = channel_posts.filter(status="pending").exists()
    status_found = is_pending


    failed_post = [cp for cp in channel_posts if cp.status == "failed"]

    process_failed_post = [cp for cp in channel_posts if cp.status == "process_failed"]
    
    if not status_found:
        is_some_failed = len(failed_post) > 0 and len(failed_post) != len(
            channel_posts_list
        )
        status_found = is_some_failed
    
    if not status_found:
        is_some_process_failed = len(process_failed_post) > 0 and len(
            process_failed_post
        ) != len(channel_posts_list)
        status_found = is_some_process_failed

    if not status_found:
        is_all_failed = len(failed_post) > 0 and len(failed_post) == len(channel_posts_list)
        status_found = is_all_failed

    if not status_found:
        is_all_process_failed = len(process_failed_post) > 0 and len(
            process_failed_post
        ) == len(channel_posts_list)
        status_found = is_all_process_failed

    message = ''
    title = ''

    if is_pending:
        post.status = "pending"
        

    if is_some_failed or is_some_process_failed:
        post.status = "partial"
        message = 'Post published but failed to publish to some channels'
        title = 'Post Published'
        

    if is_all_failed:
        post.status = "failed"
        message = 'Post failed to publish'
        title = 'Post Failed'
        

    if is_all_process_failed:
        post.status = "process_failed"
        message = 'Post failed to publish'
        title = 'Post Failed'
        

    if not (
        is_pending
        or is_some_failed
        or is_some_process_failed
        or is_all_failed
        or is_all_process_failed
    ):
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        message = "Post published successfully"
        title = 'Post Published'
        
    post.save()

    # for push notification
    if not is_pending:
        frontend_url = settings.FRONTEND_BASE_URL

        users = list(WorkspaceMember.objects.filter(workspace=workspace, is_active=True).values_list('user', flat=True))

        notification = Notification.objects.create(title=title, body=message, redirect_url=f'{frontend_url}/{workspace.slug_url}/post/{post.id}/')

        send_notification.delay(notification_type ='post_published', users=users, notification_id=notification.id)


@shared_task
def publish_scheduled_post():
    now = datetime.now(timezone.utc)

    posts = Post.objects.prefetch_related("channel_posts").filter(
        status="scheduled", schedule_date_time__lte=now, is_active=True
    )

    post_list = list(posts.all())

    for post in post_list:
        channel_posts = list(post.channel_posts.all())

        post.status = 'pending'
        post.save()

        for cp in channel_posts:
            post_to_each_channel.delay(channel_post_id=cp.id, post_id=post.id)
