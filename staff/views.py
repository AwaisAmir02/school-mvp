from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from audit.choices import AuditAction
from audit.services import log_action
from common.mixins import HtmxModalFormMixin, HtmxTemplateMixin, TenantCreateMixin, TenantFormMixin, TenantQuerysetMixin
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin
from staff.forms import StaffActivationForm, StaffForm
from staff.models import Staff
from staff.services import StaffActivationError, activate_staff, deactivate_staff, reactivate_staff


class StaffPermissionMixin(PermissionRequiredMixin):
    permission_name = Perm.MANAGE_STAFF


class StaffListView(StaffPermissionMixin, TenantQuerysetMixin, HtmxTemplateMixin, generic.ListView):
    model = Staff
    template_name = 'staff/staff_list.html'
    htmx_template_name = 'staff/_staff_table.html'
    context_object_name = 'staff_members'
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().select_related('user').order_by('first_name', 'last_name')


class StaffCreateView(StaffPermissionMixin, TenantCreateMixin, TenantFormMixin, HtmxModalFormMixin, generic.CreateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/_staff_form.html'
    success_url = reverse_lazy('staff:staff_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.CREATE, target=self.object)
        return response


class StaffUpdateView(StaffPermissionMixin, TenantQuerysetMixin, TenantFormMixin, HtmxModalFormMixin, generic.UpdateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/_staff_form.html'
    success_url = reverse_lazy('staff:staff_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.UPDATE, target=self.object)
        return response


class StaffActivateView(StaffPermissionMixin, TenantQuerysetMixin, generic.FormView):
    form_class = StaffActivationForm
    template_name = 'staff/_staff_activate_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.staff = get_object_or_404(Staff.objects.for_school(self.get_school()), pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_member'] = self.staff
        return context

    def form_valid(self, form):
        try:
            activate_staff(self.staff, form.cleaned_data['username'], form.cleaned_data['password'])
        except StaffActivationError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        log_action(actor=self.request.user, action=AuditAction.ACTIVATE, target=self.staff)
        if getattr(self.request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': 'refresh-list'})
        return redirect('staff:staff_list')


class StaffToggleActiveView(StaffPermissionMixin, TenantQuerysetMixin, generic.View):
    def post(self, request, *args, **kwargs):
        staff = get_object_or_404(Staff.objects.for_school(self.get_school()), pk=kwargs['pk'])
        if staff.is_active:
            deactivate_staff(staff)
            log_action(actor=request.user, action=AuditAction.DEACTIVATE, target=staff)
        else:
            reactivate_staff(staff)
            log_action(actor=request.user, action=AuditAction.ACTIVATE, target=staff)
        if getattr(request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': 'refresh-list'})
        return redirect('staff:staff_list')
