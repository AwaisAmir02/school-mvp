from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.choices import Role
from accounts.models import User
from common.forms import StyledFormMixin

SCHOOL_ROLE_CHOICES = [
    (Role.SCHOOL_ADMIN, Role.SCHOOL_ADMIN.label),
    (Role.TEACHER, Role.TEACHER.label),
    (Role.STAFF, Role.STAFF.label),
]


class TenantAuthenticationForm(StyledFormMixin, AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.school_id and not user.school.is_active:
            raise forms.ValidationError(
                'This school account has been deactivated. Contact your administrator.',
                code='school_inactive',
            )


class SchoolUserCreateForm(StyledFormMixin, UserCreationForm):
    role = forms.ChoiceField(choices=SCHOOL_ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number')


class SchoolUserUpdateForm(StyledFormMixin, forms.ModelForm):
    role = forms.ChoiceField(choices=SCHOOL_ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active')
