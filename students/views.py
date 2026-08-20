from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from audit.choices import AuditAction
from audit.services import log_action
from common.mixins import HtmxModalFormMixin, HtmxTemplateMixin, TenantCreateMixin, TenantFormMixin, TenantQuerysetMixin
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin
from students.forms import StudentForm, StudentImportForm
from students.imports import StudentImportError, build_template_workbook, import_students
from students.models import Student


class StudentsPermissionMixin(PermissionRequiredMixin):
    permission_name = Perm.MANAGE_STUDENTS


class StudentListView(StudentsPermissionMixin, TenantQuerysetMixin, HtmxTemplateMixin, generic.ListView):
    model = Student
    template_name = 'students/student_list.html'
    htmx_template_name = 'students/_student_table.html'
    context_object_name = 'students'
    paginate_by = 25

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('class_level', 'section', 'academic_year')
            .order_by('first_name', 'last_name')
        )


class StudentCreateView(StudentsPermissionMixin, TenantCreateMixin, TenantFormMixin, HtmxModalFormMixin, generic.CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/_student_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.CREATE, target=self.object)
        return response


class StudentUpdateView(
    StudentsPermissionMixin, TenantQuerysetMixin, TenantFormMixin, HtmxModalFormMixin, generic.UpdateView
):
    model = Student
    form_class = StudentForm
    template_name = 'students/_student_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(actor=self.request.user, action=AuditAction.UPDATE, target=self.object)
        return response


class StudentDeleteView(StudentsPermissionMixin, TenantQuerysetMixin, generic.DeleteView):
    model = Student

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        log_action(actor=request.user, action=AuditAction.DELETE, target=self.object, metadata={
            'admission_number': self.object.admission_number,
            'class_level': self.object.class_level.name,
            'section': self.object.section.name if self.object.section else None,
            'academic_year': self.object.academic_year.name,
        })
        self.object.delete()
        if getattr(request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': 'refresh-list'})
        return HttpResponse(status=204)


class StudentImportView(StudentsPermissionMixin, TenantQuerysetMixin, TenantFormMixin, generic.FormView):
    form_class = StudentImportForm
    template_name = 'students/import.html'

    def form_valid(self, form):
        school = self.get_school()
        try:
            summary = import_students(
                file=form.cleaned_data['file'],
                school=school,
                academic_year=form.cleaned_data['academic_year'],
            )
        except StudentImportError as exc:
            form.add_error('file', str(exc))
            return self.form_invalid(form)
        log_action(
            actor=self.request.user,
            action=AuditAction.IMPORT,
            school=school,
            metadata={'total': summary.total_rows, 'created': summary.created_count, 'errors': summary.error_count},
        )
        return render(self.request, 'students/import_summary.html', {'summary': summary})


class StudentImportTemplateView(StudentsPermissionMixin, generic.View):
    def get(self, request):
        workbook = build_template_workbook()
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="student_import_template.xlsx"'
        workbook.save(response)
        return response
