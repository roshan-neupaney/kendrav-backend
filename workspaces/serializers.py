from .models import (
    Workspace,
    WorkspaceTypeChoices,
    WorkspaceMember,
    WorkspaceMemberRole,
    Role,
    RolePermission,
    Permission,
)
from rest_framework import serializers
from .utils import generate_workspace_slug
from django.contrib.auth import get_user_model
from users.serializers import ProfileSerializer

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
        roles = Role.objects.filter(role_members__workspace_member=instance)
        return RoleSerializer(roles, many=True).data

    def get_permissions(self, instance):
        permissions = []
        member_roles_id = (
            instance.member_roles.select_related("role")
            .all()
            .values_list("role_id", flat=True)
        )

        role_permissions = RolePermission.objects.select_related("permission").filter(
            role_id__in=member_roles_id
        )
        role_permissions = list(role_permissions)
        for item in role_permissions:
            permissions.append(item.permission)

        member_permissions = instance.member_permissions.select_related(
            "permission"
        ).all()
        member_permissions = list(member_permissions)

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
        fields = ["id", "user", "is_active", "roles", "permissions"]
