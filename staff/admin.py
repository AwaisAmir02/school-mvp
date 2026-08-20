from django.contrib import admin

from staff.models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school', 'designation', 'role', 'is_active', 'is_activated')
    list_filter = ('school', 'role', 'is_active')
    search_fields = ('first_name', 'last_name', 'employee_code', 'email')
