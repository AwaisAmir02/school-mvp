from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from permissions.registry import user_has_permission


class PermissionRequiredMixin(LoginRequiredMixin):
    permission_name = None

    def get_permission_name(self):
        if self.permission_name is None:
            raise NotImplementedError(f'{self.__class__.__name__} must set permission_name')
        return self.permission_name

    def test_permission(self):
        return user_has_permission(self.request.user, self.get_permission_name())

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.test_permission():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
