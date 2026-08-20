from django.views import generic

from audit.models import AuditLog
from common.mixins import HtmxTemplateMixin, TenantQuerysetMixin
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin


class AuditLogListView(PermissionRequiredMixin, TenantQuerysetMixin, HtmxTemplateMixin, generic.ListView):
    model = AuditLog
    permission_name = Perm.VIEW_AUDIT_LOG
    template_name = 'audit/audit_log_list.html'
    htmx_template_name = 'audit/_audit_log_table.html'
    context_object_name = 'audit_logs'
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().select_related('actor').order_by('-created_at')
