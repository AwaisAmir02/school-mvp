from django.shortcuts import get_object_or_404

from common.exceptions import TenantMismatchError


class TenantService:
    model = None

    def __init__(self, school):
        self.school = school

    def get_queryset(self):
        return self.model.objects.for_school(self.school)

    def get_or_404(self, **lookup):
        return get_object_or_404(self.get_queryset(), **lookup)

    def create(self, **fields):
        return self.model.objects.create(school=self.school, **fields)

    def update(self, instance, **fields):
        self.assert_owned(instance)
        for field, value in fields.items():
            setattr(instance, field, value)
        instance.save(update_fields=list(fields.keys()))
        return instance

    def delete(self, instance):
        self.assert_owned(instance)
        instance.delete()

    def assert_owned(self, instance):
        if instance.school_id != self.school.id:
            raise TenantMismatchError(
                f'{instance.__class__.__name__} {instance.pk} does not belong to school {self.school.id}'
            )
