from django.db import models


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', 'Create'
    UPDATE = 'UPDATE', 'Update'
    DELETE = 'DELETE', 'Delete'
    ACTIVATE = 'ACTIVATE', 'Activate'
    DEACTIVATE = 'DEACTIVATE', 'Deactivate'
    PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Permission Change'
    IMPORT = 'IMPORT', 'Import'
    LOGIN = 'LOGIN', 'Login'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
    LOGOUT = 'LOGOUT', 'Logout'
