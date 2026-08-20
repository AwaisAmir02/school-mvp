from django import forms

from academics.models import AcademicYear, ClassLevel, Section, Stream
from common.forms import SchoolScopedModelForm


class AcademicYearForm(SchoolScopedModelForm):
    unique_together_fields = ('name',)

    class Meta:
        model = AcademicYear
        fields = ('name', 'start_date', 'end_date', 'is_current')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after the start date.')
        return cleaned_data


class ClassLevelForm(SchoolScopedModelForm):
    unique_together_fields = ('name',)

    class Meta:
        model = ClassLevel
        fields = ('name', 'order')


class StreamForm(SchoolScopedModelForm):
    unique_together_fields = ('name',)

    class Meta:
        model = Stream
        fields = ('name',)


class SectionForm(SchoolScopedModelForm):
    unique_together_fields = ('class_level', 'name')

    class Meta:
        model = Section
        fields = ('class_level', 'stream', 'name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_level'].queryset = ClassLevel.objects.for_school(self.school)
        self.fields['stream'].queryset = Stream.objects.for_school(self.school)
        self.fields['stream'].required = False
