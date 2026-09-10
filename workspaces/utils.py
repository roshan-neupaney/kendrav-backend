from django.utils.text import slugify
from django.utils.crypto import get_random_string
import logging
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def generate_workspace_slug(title, workspace_id):
    slug_id = get_random_string(length=6)
    return slugify(f"{title}-{slug_id}-{workspace_id}")


def send_invite_email(
    inviter_name, workspace_title, role_title, invite_link, expires_at, recipient_email
):
    subject = f"You've been invited to join {workspace_title} on Kendrav"
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563EB;">Kendrav</h2>
        <p>Hi there!</p>
        <p><strong>{inviter_name}</strong> has invited you to join <strong>{workspace_title}</strong> as a <strong>{role_title}</strong>.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{invite_link}" 
               style="background: #2563EB; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
                Accept Invitation
            </a>
        </div>
        <p style="color: #64748b; font-size: 14px;">This invitation expires on {expires_at.strftime("%B %d, %Y")}.</p>
        <p style="color: #64748b; font-size: 14px;">If you didn't expect this invitation, you can ignore this email.</p>
        <p style="color: #64748b; font-size: 14px;">Or copy this link: {invite_link}</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">© 2026 Kendrav. All rights reserved.</p>
    </div>
    """
    try:
        send_mail(
            subject=subject,
            message=f"You've been invited to join {workspace_title}.Accept  here: {invite_link}",
            from_email="noreply@kendrav.com",
            recipient_list=[recipient_email],
            html_message=html_message,
            # fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send invite email to {recipient_email}: {e}")
