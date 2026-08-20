from django.contrib import admin

from students.models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'admission_number', 'school', 'class_level', 'section', 'academic_year', 'is_active')
    list_filter = ('school', 'academic_year', 'class_level', 'is_active')
    search_fields = ('first_name', 'last_name', 'admission_number')
