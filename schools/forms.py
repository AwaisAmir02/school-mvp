from django import forms

from common.forms import StyledFormMixin
from schools.models import School


class SchoolProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = School
        fields = ('name', 'address', 'contact_email', 'contact_phone')


class SchoolForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = School
        fields = ('name', 'code', 'address', 'contact_email', 'contact_phone')
