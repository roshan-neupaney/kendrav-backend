from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "plan_name",
        "max_channels",
        "queue_limit",
        "allow_analytics",
        "allow_team",
        "template_type",
        "comment_and_reply",
        "activity_log",
        "custom_time_slots",
        "ai_generative_caption",
        "max_ai_generative_caption",
        "ai_generative_hastags",
        "max_ai_generative_hastags",
        "ai_generative_ideas",
        "max_ai_generative_ideas",
        "max_workspaces",
        "price",
        "duration_days",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["plan_name"]
    list_filter = ["is_active"]


