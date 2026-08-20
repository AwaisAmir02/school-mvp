from audit.models import AuditLog


def log_action(*, actor, action, target=None, school=None, metadata=None):
    if school is None and target is not None:
        school = getattr(target, 'school', None)
    if school is None and actor is not None and getattr(actor, 'is_authenticated', False):
        school = actor.school
    AuditLog.objects.create(
        school=school,
        actor=actor if actor is not None and getattr(actor, 'is_authenticated', False) else None,
        action=action,
        target_type=target.__class__.__name__ if target is not None else '',
        target_id=str(getattr(target, 'pk', '') or ''),
        target_repr=str(target) if target is not None else '',
        metadata=metadata or {},
    )
