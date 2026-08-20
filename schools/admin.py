from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    actions = ['activate_schools', 'deactivate_schools']

    @admin.action(description='Activate selected schools')
    def activate_schools(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected schools')
    def deactivate_schools(self, request, queryset):
        queryset.update(is_active=False)
