from .models import (
    Workspace,
    WorkspaceTypeChoices,
    WorkspaceMember,
    Role,
    RolePermission,
    Permission,
    WorkspaceMemberInvite,
)
from rest_framework import serializers
from .utils import generate_workspace_slug, send_invite_email
from django.contrib.auth import get_user_model
from users.serializers import ProfileSerializer
from datetime import datetime, timedelta, timezone
import secrets
from django.core.cache import cache
from django.conf import settings

User = get_user_model()


class WorkspaceSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=WorkspaceTypeChoices, required=False)
    slug_url = serializers.SlugField(required=False, read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "title", "slug_url", "type"]

    def create(self, validated_data):
        title = validated_data.pop("title")
        slug_url = generate_workspace_slug(title, "")
        workspace = Workspace.objects.create(
            title=title,
            slug_url=slug_url,
            owner=self.context["request"].user,
            type="team",
        )
        workspace.slug_url = generate_workspace_slug(title, workspace_id=workspace.id)
        workspace.save()

        WorkspaceMember.objects.create(
            user=self.context["request"].user, workspace=workspace
        )

        return workspace


class WorkspaceWithIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "title", "slug_url", "type"]

    def update(self, instance, validated_data):
        if "title" in validated_data and validated_data["title"] != instance.title:
            title = validated_data["title"]
            instance.title = title
            instance.slug_url = generate_workspace_slug(title, workspace_id=instance.id)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile",
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "title"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "title"]


class WorkspaceMemeberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_roles(self, instance):
        roles = []
        member_roles = list(instance.member_roles.all())
        roles = [item.role for item in member_roles]

        return RoleSerializer(roles, many=True).data

    def get_permissions(self, instance):
        permissions = []
        member_roles = list(instance.member_roles.all())
        member_roles_id = [item.role_id for item in member_roles]

        role_permissions = RolePermission.objects.select_related("permission").filter(
            role_id__in=member_roles_id
        )
        role_permissions = list(role_permissions)
        for item in role_permissions:
            permissions.append(item.permission)

        member_permissions = list(instance.member_permissions.all())

        permission_ids = [p.id for p in permissions]
        for item in member_permissions:
            is_revoked = item.is_revoked
            id = item.permission.id

            if id in permission_ids and is_revoked:
                permission_ids.remove(id)
            elif id not in permission_ids and not is_revoked:
                permission_ids.append(id)
                permissions.append(item.permission)

        permissions = [p for p in permissions if p.id in permission_ids]

        return PermissionSerializer(permissions, many=True).data

    class Meta:
        model = WorkspaceMember
        fields = [
            "id",
            "user",
            "is_active",
            "roles",
            "permissions",
            "created_at",
            "updated_at",
        ]


class WorkspaceMemberInviteSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    expires_at = serializers.DateTimeField(required=False)
    invited_by = serializers.CharField(required=False)

    class Meta:
        model = WorkspaceMemberInvite
        fields = [
            "id",
            "email",
            "role",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
            "invited_by",
        ]

    def create(self, validated_data):
        now = datetime.now(timezone.utc)
        workspace = self.context.get("workspace")
        user = self.context.get("user", "")
        full_name = user.profile.full_name
        workspace_title = workspace.title

        role = validated_data.get("role", "")
        role_title = role.title
        expires_at = now + timedelta(days=3)
        email = validated_data.get("email", "")

        validated_data["invited_by"] = user
        validated_data["expires_at"] = expires_at

        token = secrets.token_urlsafe(32)

        member_invite = WorkspaceMemberInvite.objects.create(
            **validated_data, workspace=workspace, token=token
        )

        frontend_url = settings.FRONTEND_BASE_URL
        invite_link = f"{frontend_url}/{workspace.slug_url}/invitation/?token={token}"
        print(full_name, workspace_title, role_title, invite_link, expires_at, email)
        send_invite_email(
            inviter_name=full_name,
            workspace_title=workspace_title,
            role_title=role_title,
            invite_link=invite_link,
            expires_at=expires_at,
            recipient_email=email,
        )

        return member_invite
