from django.db import models

from common.models import TenantScopedModel, TimeStampedModel
from students.choices import Gender


class Student(TenantScopedModel, TimeStampedModel):
    admission_number = models.CharField(max_length=30)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.PROTECT, related_name='students')
    class_level = models.ForeignKey('academics.ClassLevel', on_delete=models.PROTECT, related_name='students')
    section = models.ForeignKey(
        'academics.Section', null=True, blank=True, on_delete=models.SET_NULL, related_name='students',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'admission_number'], name='unique_admission_number_per_school'),
        ]
        indexes = [
            models.Index(fields=['school', 'academic_year', 'class_level']),
            models.Index(fields=['school', 'is_active']),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
