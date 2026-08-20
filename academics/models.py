from django.db import models
from django.db.models import Q

from common.models import TenantScopedModel, TimeStampedModel


class AcademicYear(TenantScopedModel, TimeStampedModel):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name='unique_academic_year_name_per_school'),
            models.UniqueConstraint(
                fields=['school'],
                condition=Q(is_current=True),
                name='unique_current_academic_year_per_school',
            ),
        ]
        indexes = [models.Index(fields=['school', 'is_current'])]

    def __str__(self):
        return self.name


class Stream(TenantScopedModel, TimeStampedModel):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name='unique_stream_name_per_school'),
        ]

    def __str__(self):
        return self.name


class ClassLevel(TenantScopedModel, TimeStampedModel):
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name='unique_class_level_name_per_school'),
        ]
        indexes = [models.Index(fields=['school', 'order'])]

    def __str__(self):
        return self.name


class Section(TenantScopedModel, TimeStampedModel):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='sections')
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['class_level__order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['class_level', 'name'], name='unique_section_name_per_class_level'),
        ]
        indexes = [models.Index(fields=['school', 'class_level'])]

    def __str__(self):
        return f'{self.class_level} - {self.name}'
