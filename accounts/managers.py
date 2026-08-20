from django.contrib.auth.models import UserManager as DjangoUserManager

from accounts.choices import Role
from common.managers import TenantQuerySet


class UserQuerySet(TenantQuerySet):
    pass


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', Role.SUPER_ADMIN)
        extra_fields['school'] = None
        return super().create_superuser(username, email, password, **extra_fields)
