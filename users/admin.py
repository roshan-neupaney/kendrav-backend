from django.contrib import admin
from .models import Profile, Preference, UserToken, UserSubscription, UserFcmToken


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "full_name",
        "phone_number",
        "profile_picture",
        "two_factor_enabled",
        "is_active",
        "is_email_verified",
        "created_at",
        "updated_at",
    ]
    search_fields = ["full_name", "phone_number"]
    list_filter = ["is_active"]


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "theme",
        "timezone",
        "time_format",
        "start_of_week",
        "default_posting_option",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user"]


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "refresh_token",
        "device_id",
        "device_name",
        "location",
        "last_active_at",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user", "refresh_token", "device_id", "device_name", "location"]
    list_filter = ["is_active"]

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "start_date",
        "end_date",
        "subscription",
        "payment_history_id",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user", "start_date", "end_date", "subscription"]
    list_filter = ["is_active"]

@admin.register(UserFcmToken)
class UserFcmTokenAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "fcm_token",
        "device_id",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user", "fcm_token", "device_id"]
    list_filter = ["is_active"]
