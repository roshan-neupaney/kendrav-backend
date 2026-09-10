from celery import shared_task
from .utils import send_invite_email
from .models import WorkspaceMemberInvite
from datetime import datetime, timezone

@shared_task
def send_invite_email_task(inviter_name, workspace_title, role_title, invite_link, expires_at, recipient_email):
    send_invite_email(inviter_name, workspace_title, role_title, invite_link, expires_at, recipient_email)

@shared_task
def expire_invitation_task():
    now = datetime.now(timezone.utc)
    member_invites = WorkspaceMemberInvite.objects.filter(status='pending', expires_at__lt=now)
    print(member_invites)

    if member_invites.exists:
        for invite in member_invites:
            invite.status='expired'
    # member_invites.bulk_update(member_invites, ['status'])
    WorkspaceMemberInvite.objects.bulk_update(member_invites, ['status'])