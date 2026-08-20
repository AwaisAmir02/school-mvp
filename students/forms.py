from django import forms
from django.urls import reverse_lazy

from academics.models import AcademicYear, ClassLevel, Section
from common.forms import SchoolScopedModelForm, StyledFormMixin
from students.models import Student


class StudentForm(SchoolScopedModelForm):
    unique_together_fields = ('admission_number',)

    class Meta:
        model = Student
        fields = (
            'admission_number',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'academic_year',
            'class_level',
            'section',
            'guardian_name',
            'guardian_phone',
            'email',
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.for_school(self.school)
        self.fields['class_level'].queryset = ClassLevel.objects.for_school(self.school)
        self.fields['section'].queryset = Section.objects.for_school(self.school)
        self.fields['section'].required = False
        self.fields['class_level'].widget.attrs.update({
            'hx-get': reverse_lazy('academics:section_options'),
            'hx-target': '#id_section',
            'hx-trigger': 'change',
            'hx-include': 'this',
        })

    def clean(self):
        cleaned_data = super().clean()
        class_level = cleaned_data.get('class_level')
        section = cleaned_data.get('section')
        if section and class_level and section.class_level_id != class_level.id:
            self.add_error('section', 'This section does not belong to the selected class.')
        return cleaned_data


class StudentImportForm(StyledFormMixin, forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none())
    file = forms.FileField(label='Excel file (.xlsx)')

    def __init__(self, *args, school=None, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.for_school(school)

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        if not uploaded.name.lower().endswith(('.xlsx', '.xlsm')):
            raise forms.ValidationError('Upload a valid Excel file (.xlsx).')
        return uploaded
