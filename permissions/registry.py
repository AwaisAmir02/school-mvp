from accounts.choices import Role
from permissions.constants import Perm

ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {
        Perm.MANAGE_SCHOOLS,
        Perm.MANAGE_SCHOOL_PROFILE,
        Perm.MANAGE_USERS,
        Perm.MANAGE_ACADEMICS,
        Perm.MANAGE_STAFF,
        Perm.MANAGE_STUDENTS,
        Perm.VIEW_AUDIT_LOG,
        Perm.VIEW_DASHBOARD,
    },
    Role.SCHOOL_ADMIN: {
        Perm.MANAGE_SCHOOL_PROFILE,
        Perm.MANAGE_USERS,
        Perm.MANAGE_ACADEMICS,
        Perm.MANAGE_STAFF,
        Perm.MANAGE_STUDENTS,
        Perm.VIEW_AUDIT_LOG,
        Perm.VIEW_DASHBOARD,
    },
    Role.TEACHER: {
        Perm.MANAGE_STUDENTS,
        Perm.VIEW_DASHBOARD,
    },
    Role.STAFF: {
        Perm.VIEW_DASHBOARD,
    },
}


def role_has_permission(role, perm):
    return perm in ROLE_PERMISSIONS.get(role, frozenset())


def user_has_permission(user, perm):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    return role_has_permission(user.role, perm)
