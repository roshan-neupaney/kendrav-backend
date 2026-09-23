from celery import shared_task

@shared_task
def publish_post_to_channel(post_id):
    print('hello')