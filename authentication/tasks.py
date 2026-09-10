from celery import shared_task
from .utils import send_reset_link_email, send_otp_email

@shared_task
def send_reset_link_email_task(email, reset_link):
    send_reset_link_email(email, reset_link)

@shared_task
def send_otp_email_task(email, otp):
    send_otp_email(email, otp)