from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.choices import Role
from accounts.models import User
from schools.models import School

DEMO_PASSWORD = 'Demo@12345'

DEMO_USERS = [
    ('demo_super', Role.SUPER_ADMIN),
    ('demo_admin', Role.SCHOOL_ADMIN),
    ('demo_teacher', Role.TEACHER),
    ('demo_staff', Role.STAFF),
]


class Command(BaseCommand):
    help = 'Creates a demo school and one test login per role for local UI testing.'

    def handle(self, *args, **options):
        with transaction.atomic():
            school, school_created = School.objects.get_or_create(
                code='DEMO001', defaults={'name': 'Demo School'},
            )
            if school_created:
                self.stdout.write(self.style.SUCCESS(f'Created school "{school.name}" ({school.code}).'))
            else:
                self.stdout.write(f'School "{school.name}" ({school.code}) already exists, reusing it.')

            for username, role in DEMO_USERS:
                user = User.objects.filter(username=username).first()
                if user is not None:
                    user.set_password(DEMO_PASSWORD)
                    user.save(update_fields=['password'])
                    self.stdout.write(f'User "{username}" ({role}) already exists, password reset to the demo default.')
                    continue

                if role == Role.SUPER_ADMIN:
                    User.objects.create_superuser(username=username, password=DEMO_PASSWORD)
                else:
                    User.objects.create_user(username=username, password=DEMO_PASSWORD, role=role, school=school)

                self.stdout.write(self.style.SUCCESS(f'Created user "{username}" with role {role}.'))
