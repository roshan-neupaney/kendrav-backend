from django.contrib import admin
from .models import (
    Workspace,
    Role,
    Permission,
    RolePermission,
    WorkspaceMember,
    WorkspaceMemberRole,
    WorkspaceMemberInvite,
    WorkspaceMemberPermission,
    MyTime,
)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "slug_url",
        "owner",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["title", "owner", "slug_url"]
    list_filter = ["is_active"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "workspace_id",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["title"]
    list_filter = ["is_active"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "is_active", "created_at", "updated_at"]
    search_fields = ["title"]
    list_filter = ["is_active"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "role",
        "permission",
        "created_at",
        "updated_at",
    ]
    search_fields = ["role", "permission"]


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "workspace",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user", "workspace"]
    list_filter = ["is_active"]


@admin.register(WorkspaceMemberRole)
class WorkspaceMemberRoleAdmin(admin.ModelAdmin):
    list_display = ["id", "workspace_member", "role", "created_at", "updated_at"]
    search_fields = ["workspace_member", "role"]


@admin.register(WorkspaceMemberPermission)
class WorkspaceMemberPermissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "workspace_member",
        "permission",
        "is_revoked",
        "created_at",
        "updated_at",
    ]
    search_fields = ["workspace_member"]
    list_filter = ["is_revoked"]


@admin.register(WorkspaceMemberInvite)
class WorkspaceMemberInviteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "workspace",
        "invited_by",
        "email",
        "role",
        "token",
        "status",
        "expires_at",
        "created_at",
        "updated_at",
    ]
    search_fields = ["invited_by", "email", "token", "workspace", "role"]
    list_filter = ["status"]


@admin.register(MyTime)
class MyTimeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "day",
        "time",
        "workspace",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["day", "time", "workspace"]
    list_filter = ["is_active"]
