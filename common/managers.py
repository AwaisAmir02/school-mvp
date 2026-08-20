from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(school=school)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    use_in_migrations = True
