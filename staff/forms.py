from django import forms

from accounts.models import User
from common.forms import SchoolScopedModelForm, StyledFormMixin
from staff.models import Staff


class StaffForm(SchoolScopedModelForm):
    unique_together_fields = ('employee_code',)

    class Meta:
        model = Staff
        fields = (
            'employee_code',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'designation',
            'role',
            'date_joined',
        )
        widgets = {
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
        }


class StaffActivationForm(StyledFormMixin, forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
