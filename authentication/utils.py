from django.core.mail import send_mail

logger = logging.getLogger(__name__)
# ✅ HTML email with good formatting
def send_otp_email(user_email, otp):
    subject = 'Kendrav — Password Change OTP'
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563EB;">Kendrav</h2>
        <p>You requested to change your password.</p>
        <p>Your OTP code is:</p>
        <div style="background: #f1f5f9; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <h1 style="color: #2563EB; letter-spacing: 8px; margin: 0;">{otp}</h1>
        </div>
        <p style="color: #64748b; font-size: 14px;">This OTP expires in 5 minutes. Do not share it with anyone.</p>
        <p style="color: #64748b; font-size: 14px;">If you didn't request this, ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">© 2026 Kendrav. All rights reserved.</p>
    </div>
    """
    send_mail(
        subject=subject,
        message=f"Your OTP is: {otp}",  # plain text fallback
        from_email='noreply@kendrav.com',
        recipient_list=[user_email],
        html_message=html_message
    )

def send_reset_link_email(user_email, reset_link):
    subject = 'Kendrav — Reset Your Password'
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563EB;">Kendrav</h2>
        <p>You requested to reset your password.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" 
               style="background: #2563EB; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
                Reset Password
            </a>
        </div>
        <p style="color: #64748b; font-size: 14px;">This link expires in 10 minutes.</p>
        <p style="color: #64748b; font-size: 14px;">If you didn't request this, ignore this email.</p>
        <p style="color: #64748b; font-size: 14px;">Or copy this link: {reset_link}</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">© 2026 Kendrav. All rights reserved.</p>
    </div>
    """
    try:
        send_mail(
            subject=subject,
            message=f"Reset your password: {reset_link}",  # plain text fallback
            from_email='noreply@kendrav.com',
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send reset email to {email}: {e}")