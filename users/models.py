from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


TimeFormatChoices = [
    ("12h", "12-hour"),
    ("24h", "24-hour"),
]
WeekChoices = [
    ("Sunday", "Sunday"),
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
]
PostingChoices = [
    ("next-available", "Next Available"),
    ("now", "Now"),
    ("set_date_time", "Set Date & Time"),
]
PlanChoices = [
    ("free", "Free"),
    ("pro", "Pro"),
    ("enterprise", "Enterprise"),
]
ThemeChoices = [("light", "Light"), ("dark", "Dark"), ("system", "System")]


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    backup_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.CharField(max_length=300, blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Preferences(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences"
    )
    theme = models.CharField(max_length=20, default="light", choices=ThemeChoices)
    timezone = models.CharField(max_length=50, default="UTC")
    time_format = models.CharField(
        max_length=10, default="24h", choices=TimeFormatChoices
    )
    start_of_week = models.CharField(
        max_length=10, default="Sunday", choices=WeekChoices
    )
    default_posting_option = models.CharField(
        max_length=20, default="now", choices=PostingChoices
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class UserTokens(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tokens")
    refresh_token = models.TextField()
    device_id = models.CharField(max_length=255, blank=True, null=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserSubscriptions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_subscriptions")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    subscription = models.ForeignKey('subscriptions.Subscriptions', on_delete=models.CASCADE, related_name="user_subscriptions")
    payment_history = models.ForeignKey('payments.PaymentHistory', on_delete=models.SET_NULL, blank=True, null=True, related_name="user_subscriptions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserFcmTokens(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_fcm_tokens")
    fcm_token = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
