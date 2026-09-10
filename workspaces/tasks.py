from celery import shared_task
from .utils import send_invite_email

@shared_task
def send_invite_email_task(inviter_name, workspace_title, role_title, invite_link, expires_at, recipient_email):
    send_invite_email(inviter_name, workspace_title, role_title, invite_link, expires_at, recipient_email)