from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'school', 'is_active', 'is_staff')
    list_filter = ('role', 'school', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Tenant', {'fields': ('school', 'role', 'phone_number')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Tenant', {'fields': ('school', 'role', 'phone_number')}),
    )
