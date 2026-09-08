from .models import (
    Workspace,
    WorkspaceTypeChoices,
    WorkspaceMember,
    Role,
    RolePermission,
    Permission,
    WorkspaceMemberInvite,
    WorkspaceMemberRole,
)
from rest_framework import serializers
from .utils import generate_workspace_slug, send_invite_email
from django.contrib.auth import get_user_model
from users.serializers import ProfileSerializer
from datetime import datetime, timedelta, timezone
import secrets
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
    workspace_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WorkspaceMemberInvite
        fields = [
            "id",
            "email",
            "role",
            "status",
            "workspace_id",
            "expires_at",
            "created_at",
            "updated_at",
            "invited_by",
        ]

    def create(self, validated_data):
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=3)
        user = self.context.get("user", "")

        validated_data["invited_by"] = user
        validated_data["expires_at"] = expires_at
        workspace_id = validated_data.get('workspace_id', '')

        workspace = Workspace.objects.filter(id=workspace_id).first()
        if not workspace:
            return serializers.ValidationError("Workspace not found")

        full_name = user.profile.full_name
        workspace_title = workspace.title

        role = validated_data.get("role", "")
        role_title = role.title
        email = validated_data.get("email", "")

        token = secrets.token_urlsafe(32)

        member_invite = WorkspaceMemberInvite.objects.create(
            **validated_data, workspace=workspace, token=token
        )

        frontend_url = settings.FRONTEND_BASE_URL
        invite_link = f"{frontend_url}/invitation/?token={token}"
        send_invite_email(
            inviter_name=full_name,
            workspace_title=workspace_title,
            role_title=role_title,
            invite_link=invite_link,
            expires_at=expires_at,
            recipient_email=email,
        )

        return member_invite


class MemberInviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token = attrs.get("token", "")
        user = self.context.get("user", "")
        member_invite = WorkspaceMemberInvite.objects.filter(token=token).first()

        if (
            member_invite is None
            or member_invite.status == "accepted"
            or member_invite.status == "declined"
        ):
            raise serializers.ValidationError("Invitation does not exists")

        if member_invite.email != user.email:
            raise serializers.ValidationError("Unauthorized Request")

        if member_invite.status == "expired":
            raise serializers.ValidationError("Invitation has expired")

        now = datetime.now(timezone.utc)
        expires_at = member_invite.expires_at
        if now > expires_at:
            member_invite.status = "expired"
            member_invite.save()
            raise serializers.ValidationError("Invitation has expired")

        return {"member_invite": member_invite}

    def create(self, validated_data):
        member_invite = validated_data.get("member_invite")
        user = self.context.get("user")

        workspace = member_invite.workspace
        role = member_invite.role

        workspace_member, _created = WorkspaceMember.objects.get_or_create(
            user=user, workspace_id=workspace.id
        )
        WorkspaceMemberRole.objects.get_or_create(
            workspace_member=workspace_member, role=role
        )

        member_invite.status = "accepted"
        member_invite.save()

        return workspace_member