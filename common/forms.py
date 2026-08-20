from django import forms

TEXT_INPUT_CLASS = 'form-control'
SELECT_CLASS = 'form-select'
CHECKBOX_CLASS = 'form-check-input'


def style_form_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault('class', CHECKBOX_CLASS)
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.setdefault('class', SELECT_CLASS)
        else:
            widget.attrs.setdefault('class', TEXT_INPUT_CLASS)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class SchoolScopedModelForm(StyledFormMixin, forms.ModelForm):
    unique_together_fields = ()

    def __init__(self, *args, school=None, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.unique_together_fields and self.school:
            lookup = {field: cleaned_data.get(field) for field in self.unique_together_fields}
            if all(value is not None for value in lookup.values()):
                queryset = self._meta.model.objects.for_school(self.school).filter(**lookup)
                if self.instance.pk:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    field_names = ', '.join(self.unique_together_fields)
                    raise forms.ValidationError(f'A record with this {field_names} already exists for this school.')
        return cleaned_data
