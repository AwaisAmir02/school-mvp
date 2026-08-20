from django.contrib.auth import views as auth_views
from django.urls import reverse, reverse_lazy
from django.views import generic

from accounts.forms import SchoolUserCreateForm, SchoolUserUpdateForm, TenantAuthenticationForm
from accounts.models import User
from audit.choices import AuditAction
from audit.services import log_action
from common.mixins import HtmxModalFormMixin, HtmxTemplateMixin, TenantCreateMixin, TenantQuerysetMixin
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = TenantAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse('admin:index')
        return reverse('schools:dashboard')


class LogoutView(auth_views.LogoutView):
    pass


class UserListView(PermissionRequiredMixin, TenantQuerysetMixin, HtmxTemplateMixin, generic.ListView):
    model = User
    permission_name = Perm.MANAGE_USERS
    template_name = 'accounts/user_list.html'
    htmx_template_name = 'accounts/_user_table.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().order_by('username')


class UserCreateView(PermissionRequiredMixin, TenantCreateMixin, HtmxModalFormMixin, generic.CreateView):
    model = User
    permission_name = Perm.MANAGE_USERS
    form_class = SchoolUserCreateForm
    template_name = 'accounts/_user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.CREATE, target=self.object)
        return response


class UserUpdateView(PermissionRequiredMixin, TenantQuerysetMixin, HtmxModalFormMixin, generic.UpdateView):
    model = User
    permission_name = Perm.MANAGE_USERS
    form_class = SchoolUserUpdateForm
    template_name = 'accounts/_user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        previous = User.objects.get(pk=self.object.pk)
        previous_role, previous_is_active = previous.role, previous.is_active
        response = super().form_valid(form)

        if self.object.role != previous_role:
            log_action(
                actor=self.request.user, action=AuditAction.PERMISSION_CHANGE, target=self.object,
                metadata={'previous_role': previous_role, 'new_role': self.object.role},
            )
        if previous_is_active and not self.object.is_active:
            log_action(actor=self.request.user, action=AuditAction.DEACTIVATE, target=self.object)
        elif not previous_is_active and self.object.is_active:
            log_action(actor=self.request.user, action=AuditAction.ACTIVATE, target=self.object)
        elif self.object.role == previous_role:
            log_action(actor=self.request.user, action=AuditAction.UPDATE, target=self.object)

        return response
