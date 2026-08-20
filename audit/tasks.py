from datetime import timedelta

from celery import shared_task
from decouple import config
from django.utils import timezone

from audit.models import AuditLog


@shared_task
def purge_stale_audit_logs():
    retention_days = config('AUDIT_LOG_RETENTION_DAYS', default=365, cast=int)
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted_count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    return deleted_count
