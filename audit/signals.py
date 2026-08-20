from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver

from audit.choices import AuditAction
from audit.services import log_action


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    log_action(actor=user, action=AuditAction.LOGIN, target=user, school=user.school)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if user is not None:
        log_action(actor=user, action=AuditAction.LOGOUT, target=user, school=user.school)


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request=None, **kwargs):
    log_action(actor=None, action=AuditAction.LOGIN_FAILED, metadata={'username': credentials.get('username', '')})
