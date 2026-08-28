import time

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from accounts.choices import Role
from accounts.models import User
from common.management.commands.seed_demo_data import DEMO_EMAIL_DOMAIN, DEMO_PASSWORD, create_school_admin
from schools.models import School


class Command(BaseCommand):
    help = (
        'Backfills one School Admin User per already-existing demo school (code__startswith="CDEMO"). '
        'Does not create schools, teachers, or students - run seed_demo_data for that. Safe to re-run.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        schools = list(School.objects.filter(code__startswith='CDEMO').order_by('code'))
        existing_admin_school_ids = set(
            User.objects.filter(school__in=schools, role=Role.SCHOOL_ADMIN).values_list('school_id', flat=True)
        )
        pending_schools = [school for school in schools if school.id not in existing_admin_school_ids]

        if options['dry_run']:
            self.stdout.write(
                f'{len(schools)} demo schools found, {len(schools) - len(pending_schools)} already have a '
                f'School Admin.'
            )
            self.stdout.write(f'Would create {len(pending_schools)} School Admin User records '
                               f'(usernames derived from each school\'s CDEMO number, e.g. CDEMO001 -> '
                               f'demo.admin0001, password "{DEMO_PASSWORD}", emails @{DEMO_EMAIL_DOMAIN}).')
            return

        if not pending_schools:
            self.stdout.write('Every demo school already has a School Admin, nothing to do.')
            return

        fake = Faker()
        started = time.monotonic()

        with transaction.atomic():
            for school in pending_schools:
                index = int(school.code.removeprefix('CDEMO'))
                create_school_admin(fake, school, index)

        elapsed = time.monotonic() - started
        self.stdout.write(self.style.SUCCESS(
            f'Created {len(pending_schools)} School Admin accounts in {elapsed:.1f}s.'
        ))
