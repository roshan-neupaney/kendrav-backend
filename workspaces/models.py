from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

StatusChoices = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('declined', 'Declined'),
    ('expired', 'Expired')
]

DayChoices = [
    ('Sunday', 'Sunday'),
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
]

WorkspaceTypeChoices = [
    ('personal', 'Personal'),
    ('team', 'Team'),
]

class Workspace(models.Model):
    title= models.CharField(max_length=255)
    slug_url= models.SlugField(max_length=255, unique=True)
    owner= models.ForeignKey(User, on_delete=models.CASCADE, related_name="workspaces")
    type= models.CharField(max_length=20, choices=WorkspaceTypeChoices)
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class Role(models.Model):
    title= models.CharField(max_length=100)
    workspace= models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="roles", blank=True, null=True)
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class Permission(models.Model):
    title= models.CharField(max_length=100)
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class RolePermission(models.Model):
    role= models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission= models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class WorkspaceMember(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_workspaces")
    workspace= models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="workspace_members")
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class WorkspaceMemberRole(models.Model):
    workspace_member= models.ForeignKey(WorkspaceMember, on_delete=models.CASCADE, related_name="member_roles")
    role= models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_members")
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class WorkspaceMemberPermission(models.Model):
    workspace_member= models.ForeignKey(WorkspaceMember, on_delete=models.CASCADE, related_name="member_permissions")
    permission= models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_members")
    is_revoked= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class WorkspaceMemberInvite(models.Model):
    workspace= models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="member_invites")
    invited_by= models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_invites")
    email= models.EmailField()
    role= models.ForeignKey(Role, on_delete=models.CASCADE, related_name="invites")
    token= models.CharField(max_length=255, unique=True)
    status= models.CharField(max_length=20, choices=StatusChoices, default='pending')
    expires_at= models.DateTimeField()
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

class MyTime(models.Model):
    day= models.CharField(max_length=20, choices=DayChoices)
    time= models.TimeField()
    workspace= models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="my_times")
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)
