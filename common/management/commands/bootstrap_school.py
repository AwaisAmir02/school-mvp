from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.choices import Role
from accounts.models import User
from schools.models import School


class Command(BaseCommand):
    help = 'Bootstraps the single School record and its first School Admin for single-school deployments.'

    def add_arguments(self, parser):
        parser.add_argument('--name', default=None)
        parser.add_argument('--code', default=None)
        parser.add_argument('--admin-username', default=None)
        parser.add_argument('--admin-password', default=None)
        parser.add_argument('--admin-email', default=None)

    def handle(self, *args, **options):
        if not settings.SINGLE_SCHOOL_MODE:
            raise CommandError(
                'SINGLE_SCHOOL_MODE is disabled. Use Django admin to manage schools in multi-tenant mode.'
            )

        name = options['name'] or config('SCHOOL_NAME', default='')
        code = options['code'] or config('SCHOOL_CODE', default='')
        if not name or not code:
            raise CommandError('SCHOOL_NAME and SCHOOL_CODE must be provided via options or environment variables.')

        with transaction.atomic():
            school, created = School.objects.get_or_create(code=code, defaults={'name': name})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created school "{school.name}" ({school.code}).'))
            else:
                self.stdout.write(f'School "{school.name}" ({school.code}) already exists, reusing it.')

            admin_username = options['admin_username'] or config('SCHOOL_ADMIN_USERNAME', default='')
            admin_password = options['admin_password'] or config('SCHOOL_ADMIN_PASSWORD', default='')
            admin_email = options['admin_email'] or config('SCHOOL_ADMIN_EMAIL', default='')

            if admin_username and admin_password:
                if User.objects.filter(username=admin_username).exists():
                    self.stdout.write(f'User "{admin_username}" already exists, skipping admin creation.')
                else:
                    User.objects.create_user(
                        username=admin_username, password=admin_password, email=admin_email,
                        role=Role.SCHOOL_ADMIN, school=school,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created School Admin "{admin_username}".'))
            else:
                self.stdout.write('No admin credentials provided; skipping School Admin creation.')
