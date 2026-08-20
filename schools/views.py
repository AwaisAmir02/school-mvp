from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from academics.models import AcademicYear, ClassLevel, Section
from accounts.models import User
from audit.choices import AuditAction
from audit.services import log_action
from common.mixins import HtmxModalFormMixin, HtmxTemplateMixin, TenantQuerysetMixin
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin
from schools.forms import SchoolForm, SchoolProfileForm
from schools.models import School
from staff.models import Staff
from students.models import Student


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'schools/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('admin:index')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.request.user.school
        context['school'] = school
        context['staff_count'] = Staff.objects.for_school(school).filter(is_active=True).count()
        context['pending_activation_count'] = Staff.objects.for_school(school).filter(user__isnull=True).count()
        context['class_level_count'] = ClassLevel.objects.for_school(school).count()
        context['section_count'] = Section.objects.for_school(school).count()
        context['student_count'] = Student.objects.for_school(school).filter(is_active=True).count()
        context['current_academic_year'] = AcademicYear.objects.for_school(school).filter(is_current=True).first()
        return context


class SchoolProfileUpdateView(PermissionRequiredMixin, TenantQuerysetMixin, generic.UpdateView):
    model = School
    form_class = SchoolProfileForm
    permission_name = Perm.MANAGE_SCHOOL_PROFILE
    template_name = 'schools/profile.html'
    success_url = reverse_lazy('schools:profile')

    def get_object(self, queryset=None):
        return self.get_school()

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.UPDATE, target=self.object)
        return response


class SuperAdminPermissionMixin(PermissionRequiredMixin):
    permission_name = Perm.MANAGE_SCHOOLS


class SuperAdminDashboardView(SuperAdminPermissionMixin, generic.TemplateView):
    template_name = 'schools/super_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school_count'] = School.objects.count()
        context['active_school_count'] = School.objects.filter(is_active=True).count()
        context['user_count'] = User.objects.count()
        context['student_count'] = Student.objects.count()
        return context


class SchoolListView(SuperAdminPermissionMixin, HtmxTemplateMixin, generic.ListView):
    model = School
    template_name = 'schools/school_list.html'
    htmx_template_name = 'schools/_school_table.html'
    context_object_name = 'schools'
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().annotate(user_count=Count('users')).order_by('name')


class SchoolCreateView(SuperAdminPermissionMixin, HtmxModalFormMixin, generic.CreateView):
    model = School
    form_class = SchoolForm
    template_name = 'schools/_school_form.html'
    success_url = reverse_lazy('schools:school_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.CREATE, target=self.object)
        return response


class SchoolUpdateView(SuperAdminPermissionMixin, HtmxModalFormMixin, generic.UpdateView):
    model = School
    form_class = SchoolForm
    template_name = 'schools/_school_form.html'
    success_url = reverse_lazy('schools:school_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.UPDATE, target=self.object)
        return response


class SchoolToggleActiveView(SuperAdminPermissionMixin, generic.View):
    def post(self, request, *args, **kwargs):
        school = get_object_or_404(School, pk=kwargs['pk'])
        school.is_active = not school.is_active
        school.save(update_fields=['is_active'])
        action = AuditAction.ACTIVATE if school.is_active else AuditAction.DEACTIVATE
        log_action(actor=request.user, action=action, target=school)
        if getattr(request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': 'refresh-list'})
        return redirect('schools:school_list')
