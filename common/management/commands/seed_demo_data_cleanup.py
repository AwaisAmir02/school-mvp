from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from audit.models import AuditLog
from common.management.commands.seed_demo_data import DEMO_EMAIL_DOMAIN, DEMO_SOURCE_TAG
from schools.models import School
from staff.models import Staff
from students.models import Student


class Command(BaseCommand):
    help = 'Deletes demo data created by seed_demo_data, identified by its DEMO code prefix and email domain.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--yes', action='store_true')

    def handle(self, *args, **options):
        schools = School.objects.filter(code__startswith='CDEMO')
        users = User.objects.filter(email__iendswith=f'@{DEMO_EMAIL_DOMAIN}')
        audit_logs = AuditLog.objects.filter(metadata__source=DEMO_SOURCE_TAG)
        staff_count = Staff.objects.filter(school__in=schools).count()
        student_count = Student.objects.filter(school__in=schools).count()

        school_count = schools.count()
        user_count = users.count()
        audit_count = audit_logs.count()

        self.stdout.write(
            f'Would delete {school_count} demo schools (cascading to {staff_count} staff and '
            f'{student_count} students, plus their academic years/class levels/sections), '
            f'{user_count} demo user accounts, and {audit_count} demo audit log entries.'
        )

        if options['dry_run']:
            return

        if school_count == 0 and user_count == 0 and audit_count == 0:
            self.stdout.write('Nothing to delete.')
            return

        if not options['yes']:
            confirm = input('Type "DELETE" to permanently delete the records listed above: ')
            if confirm != 'DELETE':
                self.stdout.write('Aborted, nothing was deleted.')
                return

        with transaction.atomic():
            audit_logs.delete()
            users.delete()
            schools.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {school_count} demo schools and everything scoped to them, plus {user_count} user accounts.'
        ))
