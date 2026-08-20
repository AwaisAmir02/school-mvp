from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from permissions.registry import user_has_permission


def permission_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not user_has_permission(request.user, perm):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
