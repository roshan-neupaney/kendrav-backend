from django.db import models

SubscriptionsTypeChoices = [
    ("free", "Free"),
    ("pro", "Pro"),
    ("enterprise", "Enterprise"),
]

TemplateTypeChoices = [
    ("basic", "Basic"),
    ("full", "Full"),
]

class Subscription(models.Model):
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=SubscriptionsTypeChoices)
    max_channels = models.IntegerField()
    queue_limit = models.IntegerField()
    allow_analytics = models.BooleanField(default=False)
    allow_team = models.BooleanField(default=False)
    template_type = models.CharField(max_length=50, choices=TemplateTypeChoices)
    comment_and_reply = models.BooleanField(default=False)
    activity_log = models.BooleanField(default=False)
    custom_time_slots = models.BooleanField(default=False)
    ai_generative_caption = models.BooleanField(default=False)
    max_ai_generative_caption = models.IntegerField(default=0)
    ai_generative_hastags = models.BooleanField(default=False)
    max_ai_generative_hastags = models.IntegerField(default=0)
    ai_generative_ideas = models.BooleanField(default=False)
    max_ai_generative_ideas = models.IntegerField(default=0)
    max_workspaces = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)