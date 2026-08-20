from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from academics.forms import AcademicYearForm, ClassLevelForm, SectionForm, StreamForm
from academics.models import AcademicYear, ClassLevel, Section, Stream
from common.mixins import (
    HtmxDeleteMixin,
    HtmxModalFormMixin,
    HtmxTemplateMixin,
    TenantCreateMixin,
    TenantFormMixin,
    TenantQuerysetMixin,
)
from permissions.constants import Perm
from permissions.mixins import PermissionRequiredMixin
from permissions.registry import user_has_permission


class AcademicsPermissionMixin(PermissionRequiredMixin):
    permission_name = Perm.MANAGE_ACADEMICS


class BaseAcademicsListView(AcademicsPermissionMixin, TenantQuerysetMixin, HtmxTemplateMixin, generic.ListView):
    pass


class BaseAcademicsCreateView(
    AcademicsPermissionMixin, TenantCreateMixin, TenantFormMixin, HtmxModalFormMixin, generic.CreateView
):
    pass


class BaseAcademicsUpdateView(
    AcademicsPermissionMixin, TenantQuerysetMixin, TenantFormMixin, HtmxModalFormMixin, generic.UpdateView
):
    pass


class BaseAcademicsDeleteView(AcademicsPermissionMixin, TenantQuerysetMixin, HtmxDeleteMixin, generic.DeleteView):
    pass


class AcademicYearListView(BaseAcademicsListView):
    model = AcademicYear
    template_name = 'academics/academic_year_list.html'
    htmx_template_name = 'academics/_academic_year_table.html'
    context_object_name = 'academic_years'


class AcademicYearCreateView(BaseAcademicsCreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/_academic_year_form.html'
    success_url = reverse_lazy('academics:academic_year_list')

    def form_valid(self, form):
        with transaction.atomic():
            if form.cleaned_data.get('is_current'):
                AcademicYear.objects.for_school(self.get_school()).filter(is_current=True).update(is_current=False)
            return super().form_valid(form)


class AcademicYearUpdateView(BaseAcademicsUpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/_academic_year_form.html'
    success_url = reverse_lazy('academics:academic_year_list')

    def form_valid(self, form):
        with transaction.atomic():
            if form.cleaned_data.get('is_current'):
                AcademicYear.objects.for_school(self.get_school()).filter(
                    is_current=True
                ).exclude(pk=self.object.pk).update(is_current=False)
            return super().form_valid(form)


class AcademicYearDeleteView(BaseAcademicsDeleteView):
    model = AcademicYear


class ClassLevelListView(BaseAcademicsListView):
    model = ClassLevel
    template_name = 'academics/class_level_list.html'
    htmx_template_name = 'academics/_class_level_table.html'
    context_object_name = 'class_levels'


class ClassLevelCreateView(BaseAcademicsCreateView):
    model = ClassLevel
    form_class = ClassLevelForm
    template_name = 'academics/_class_level_form.html'
    success_url = reverse_lazy('academics:class_level_list')


class ClassLevelUpdateView(BaseAcademicsUpdateView):
    model = ClassLevel
    form_class = ClassLevelForm
    template_name = 'academics/_class_level_form.html'
    success_url = reverse_lazy('academics:class_level_list')


class ClassLevelDeleteView(BaseAcademicsDeleteView):
    model = ClassLevel


class StreamListView(BaseAcademicsListView):
    model = Stream
    template_name = 'academics/stream_list.html'
    htmx_template_name = 'academics/_stream_table.html'
    context_object_name = 'streams'


class StreamCreateView(BaseAcademicsCreateView):
    model = Stream
    form_class = StreamForm
    template_name = 'academics/_stream_form.html'
    success_url = reverse_lazy('academics:stream_list')


class StreamUpdateView(BaseAcademicsUpdateView):
    model = Stream
    form_class = StreamForm
    template_name = 'academics/_stream_form.html'
    success_url = reverse_lazy('academics:stream_list')


class StreamDeleteView(BaseAcademicsDeleteView):
    model = Stream


class SectionListView(BaseAcademicsListView):
    model = Section
    template_name = 'academics/section_list.html'
    htmx_template_name = 'academics/_section_table.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return super().get_queryset().select_related('class_level', 'stream')


class SectionCreateView(BaseAcademicsCreateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/_section_form.html'
    success_url = reverse_lazy('academics:section_list')


class SectionUpdateView(BaseAcademicsUpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/_section_form.html'
    success_url = reverse_lazy('academics:section_list')


class SectionDeleteView(BaseAcademicsDeleteView):
    model = Section


class SectionOptionsView(LoginRequiredMixin, TenantQuerysetMixin, generic.View):
    def get(self, request):
        if not (
            user_has_permission(request.user, Perm.MANAGE_ACADEMICS)
            or user_has_permission(request.user, Perm.MANAGE_STUDENTS)
        ):
            raise PermissionDenied
        class_level_id = request.GET.get('class_level')
        sections = (
            Section.objects.for_school(self.get_school()).filter(class_level_id=class_level_id)
            if class_level_id
            else Section.objects.none()
        )
        return render(request, 'academics/_section_options.html', {'sections': sections})
