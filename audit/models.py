from django.db import models

from audit.choices import AuditAction
from common.managers import TenantQuerySet
from common.models import TimeStampedModel


class AuditLogQuerySet(TenantQuerySet):
    pass


class AuditLogManager(models.Manager.from_queryset(AuditLogQuerySet)):
    pass


class AuditLog(TimeStampedModel):
    school = models.ForeignKey(
        'schools.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs',
    )
    actor = models.ForeignKey(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=AuditAction.choices)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=50, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = AuditLogManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f'{self.get_action_display()} · {self.target_type} {self.target_repr}'.strip()
