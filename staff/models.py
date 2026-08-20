from django.db import models

from accounts.choices import Role
from common.models import TenantScopedModel, TimeStampedModel

STAFF_ROLE_CHOICES = [
    (Role.TEACHER, Role.TEACHER.label),
    (Role.STAFF, Role.STAFF.label),
]


class Staff(TenantScopedModel, TimeStampedModel):
    user = models.OneToOneField(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='staff_profile',
    )
    employee_code = models.CharField(max_length=30)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES, default=Role.TEACHER)
    date_joined = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'employee_code'], name='unique_employee_code_per_school'),
        ]
        indexes = [models.Index(fields=['school', 'is_active'])]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_activated(self):
        return self.user_id is not None
