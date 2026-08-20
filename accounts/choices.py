from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    SCHOOL_ADMIN = 'SCHOOL_ADMIN', 'School Admin'
    TEACHER = 'TEACHER', 'Teacher'
    STAFF = 'STAFF', 'Staff'
