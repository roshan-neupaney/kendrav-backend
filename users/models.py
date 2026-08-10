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
