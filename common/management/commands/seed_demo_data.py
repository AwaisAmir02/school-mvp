import random
import time
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from academics.models import AcademicYear, ClassLevel, Section
from accounts.choices import Role
from accounts.models import User
from audit.choices import AuditAction
from audit.services import log_action
from schools.models import School
from staff.models import Staff
from staff.services import activate_staff
from students.choices import Gender
from students.models import Student

DEMO_EMAIL_DOMAIN = 'demo.schoolmvp.test'
DEMO_PASSWORD = 'Demo@12345'
DEMO_SOURCE_TAG = 'seed_demo_data'
SCHOOL_COUNT = 50
TEACHER_TOTAL = 200
STUDENT_TOTAL = 1000
CLASS_LEVEL_NAMES = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5']
SECTION_NAMES = ['A', 'B']
SCHOOL_TYPE_SUFFIXES = [
    'Academy', 'High School', 'Elementary School', 'Public School', 'International School', 'Preparatory School',
]


def create_school_admin(fake, school, index):
    username = f'demo.admin{index:04d}'
    user = User.objects.create_user(
        username=username,
        password=DEMO_PASSWORD,
        email=f'{username}@{DEMO_EMAIL_DOMAIN}',
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        role=Role.SCHOOL_ADMIN,
        school=school,
    )
    log_action(actor=None, action=AuditAction.CREATE, target=user, metadata={'source': DEMO_SOURCE_TAG})
    return user


def distribute(total, buckets, minimum, rng):
    counts = [total // buckets] * buckets
    for i in range(total % buckets):
        counts[i] += 1
    for _ in range(buckets * 2):
        a, b = rng.sample(range(buckets), 2)
        shift = rng.randint(1, 2)
        if counts[a] - shift >= minimum:
            counts[a] -= shift
            counts[b] += shift
    return counts


class Command(BaseCommand):
    help = (
        'Seeds realistic demo data (schools, teachers, students) for a client demo. '
        'Safe to run against the live database; remove it later with seed_demo_data_cleanup.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--seed', type=int, default=None)

    def handle(self, *args, **options):
        class_level_total = SCHOOL_COUNT * len(CLASS_LEVEL_NAMES)
        section_total = class_level_total * len(SECTION_NAMES)

        if options['dry_run']:
            self.stdout.write('DRY RUN - no database changes will be made.')
            self.stdout.write(f'Would create {SCHOOL_COUNT} School records '
                               f'(names "Client Demo School 01".."Client Demo School {SCHOOL_COUNT:02d}", '
                               f'codes CDEMO001..CDEMO{SCHOOL_COUNT:03d}).')
            self.stdout.write(f'Would create {SCHOOL_COUNT} AcademicYear, {class_level_total} ClassLevel, '
                               f'{section_total} Section records (minimal structure per school).')
            self.stdout.write(f'Would create {SCHOOL_COUNT} School Admin User records, one per school '
                               f'(usernames demo.admin0001..demo.admin{SCHOOL_COUNT:04d}, '
                               f'password "{DEMO_PASSWORD}", emails @{DEMO_EMAIL_DOMAIN}).')
            self.stdout.write(f'Would create {TEACHER_TOTAL} Staff records with role=TEACHER, '
                               f'each activated into a linked User account '
                               f'(usernames demo.teacher0001..demo.teacher{TEACHER_TOTAL:04d}, '
                               f'password "{DEMO_PASSWORD}", emails @{DEMO_EMAIL_DOMAIN}).')
            self.stdout.write(f'Would create {STUDENT_TOTAL} Student records '
                               f'(admission numbers CDEMO0001.. per school, emails @{DEMO_EMAIL_DOMAIN}).')
            self.stdout.write(f'Would write {SCHOOL_COUNT} school-creation, {SCHOOL_COUNT} School Admin creation, '
                               f'{TEACHER_TOTAL * 2} teacher create/activate audit log entries, and '
                               f'{SCHOOL_COUNT} bulk-import-style audit log entries summarizing the student batches '
                               f'(individual per-student audit entries are skipped - see help text above for why).')
            return

        rng = random.Random(options['seed'])
        fake = Faker()
        Faker.seed(options['seed'])
        started = time.monotonic()

        with transaction.atomic():
            schools = self._create_schools(fake, rng)
            academic_years, class_levels_by_school, sections_by_class_level = self._create_academic_structure(schools)
            admin_count = self._create_school_admins(fake, schools)
            teacher_count = self._create_teachers(fake, rng, schools)
            student_count = self._create_students(
                fake, rng, schools, academic_years, class_levels_by_school, sections_by_class_level,
            )

        elapsed = time.monotonic() - started
        self.stdout.write(self.style.SUCCESS(
            f'Created {len(schools)} schools, {admin_count} school admins, {teacher_count} teachers, '
            f'{student_count} students in {elapsed:.1f}s.'
        ))

    def _create_school_admins(self, fake, schools):
        for index, school in enumerate(schools, start=1):
            create_school_admin(fake, school, index)
        return len(schools)

    def _create_schools(self, fake, rng):
        pending = []
        for i in range(1, SCHOOL_COUNT + 1):
            name = f'Client Demo School {i:02d} - {fake.city()} {rng.choice(SCHOOL_TYPE_SUFFIXES)}'
            pending.append(School(
                name=name,
                slug=slugify(name),
                code=f'CDEMO{i:03d}',
                address=fake.address().replace('\n', ', '),
                contact_email=f'contact{i:03d}@{DEMO_EMAIL_DOMAIN}',
                contact_phone=fake.numerify('##########'),
                is_active=True,
            ))
        schools = School.objects.bulk_create(pending)
        for school in schools:
            log_action(actor=None, action=AuditAction.CREATE, target=school, metadata={'source': DEMO_SOURCE_TAG})
        return schools

    def _create_academic_structure(self, schools):
        academic_years = AcademicYear.objects.bulk_create([
            AcademicYear(
                school=school, name='2025-2026',
                start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True,
            )
            for school in schools
        ])

        pending_class_levels = []
        for school in schools:
            for order, level_name in enumerate(CLASS_LEVEL_NAMES, start=1):
                pending_class_levels.append(ClassLevel(school=school, name=level_name, order=order))
        class_levels = ClassLevel.objects.bulk_create(pending_class_levels)

        class_levels_by_school = {}
        for class_level in class_levels:
            class_levels_by_school.setdefault(class_level.school_id, []).append(class_level)

        pending_sections = []
        for class_level in class_levels:
            for section_name in SECTION_NAMES:
                pending_sections.append(Section(
                    school_id=class_level.school_id, class_level=class_level, name=section_name,
                ))
        sections = Section.objects.bulk_create(pending_sections)

        sections_by_class_level = {}
        for section in sections:
            sections_by_class_level.setdefault(section.class_level_id, []).append(section)

        return academic_years, class_levels_by_school, sections_by_class_level

    def _create_teachers(self, fake, rng, schools):
        counts = distribute(TEACHER_TOTAL, len(schools), minimum=2, rng=rng)
        global_index = 0
        for school, count in zip(schools, counts):
            for _ in range(count):
                global_index += 1
                username = f'demo.teacher{global_index:04d}'
                staff = Staff.objects.create(
                    school=school,
                    employee_code=f'CDEMO-T-{global_index:04d}',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=f'{username}@{DEMO_EMAIL_DOMAIN}',
                    phone_number=fake.numerify('##########'),
                    designation='Teacher',
                    role=Role.TEACHER,
                    date_joined=fake.date_between(start_date='-5y', end_date='today'),
                    is_active=True,
                )
                log_action(actor=None, action=AuditAction.CREATE, target=staff, metadata={'source': DEMO_SOURCE_TAG})
                activate_staff(staff, username, DEMO_PASSWORD)
                log_action(actor=None, action=AuditAction.ACTIVATE, target=staff, metadata={'source': DEMO_SOURCE_TAG})
        return global_index

    def _create_students(self, fake, rng, schools, academic_years, class_levels_by_school, sections_by_class_level):
        academic_year_by_school = {ay.school_id: ay for ay in academic_years}
        counts = distribute(STUDENT_TOTAL, len(schools), minimum=10, rng=rng)

        pending_students = []
        for school, count in zip(schools, counts):
            academic_year = academic_year_by_school[school.id]
            class_levels = class_levels_by_school[school.id]
            for seq in range(1, count + 1):
                class_level = rng.choice(class_levels)
                section = rng.choice(sections_by_class_level[class_level.id])
                admission_number = f'CDEMO{seq:04d}'
                pending_students.append(Student(
                    school=school,
                    admission_number=admission_number,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    date_of_birth=fake.date_of_birth(minimum_age=5, maximum_age=17),
                    gender=rng.choice(Gender.values),
                    guardian_name=fake.name(),
                    guardian_phone=fake.numerify('##########'),
                    email=f'{admission_number.lower()}.{school.code.lower()}@{DEMO_EMAIL_DOMAIN}',
                    academic_year=academic_year,
                    class_level=class_level,
                    section=section,
                    is_active=True,
                ))
            log_action(
                actor=None, action=AuditAction.IMPORT, school=school,
                metadata={'source': DEMO_SOURCE_TAG, 'student_count': count},
            )

        created = Student.objects.bulk_create(pending_students)
        return len(created)
