from permissions.constants import Perm
from permissions.registry import user_has_permission


def user_permissions(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'perms_ctx': {}}
    return {
        'perms_ctx': {
            'can_manage_school_profile': user_has_permission(user, Perm.MANAGE_SCHOOL_PROFILE),
            'can_manage_users': user_has_permission(user, Perm.MANAGE_USERS),
            'can_manage_academics': user_has_permission(user, Perm.MANAGE_ACADEMICS),
            'can_manage_staff': user_has_permission(user, Perm.MANAGE_STAFF),
            'can_manage_students': user_has_permission(user, Perm.MANAGE_STUDENTS),
            'can_view_audit_log': user_has_permission(user, Perm.VIEW_AUDIT_LOG),
        }
    }
