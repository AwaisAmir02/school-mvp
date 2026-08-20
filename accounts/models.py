from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from accounts.choices import Role
from accounts.managers import UserManager


class User(AbstractUser):
    school = models.ForeignKey(
        'schools.School',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='users',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    phone_number = models.CharField(max_length=20, blank=True)

    objects = UserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(role=Role.SUPER_ADMIN) & Q(school__isnull=True))
                    | (~Q(role=Role.SUPER_ADMIN) & Q(school__isnull=False))
                ),
                name='super_admin_has_no_school_others_require_school',
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'role']),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def is_school_admin(self):
        return self.role == Role.SCHOOL_ADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_school_staff(self):
        return self.role == Role.STAFF
