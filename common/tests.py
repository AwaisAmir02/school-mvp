import io

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.choices import Role
from accounts.models import User
from common.exceptions import TenantMismatchError
from common.services import TenantService
from schools.models import School


class UserTenantService(TenantService):
    model = User


class TenantServiceTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.service_a = UserTenantService(self.school_a)
        self.service_b = UserTenantService(self.school_b)

    def test_create_scopes_new_record_to_school(self):
        user = self.service_a.create(username='staff_a', role=Role.STAFF)
        self.assertEqual(user.school_id, self.school_a.id)

    def test_get_queryset_excludes_other_schools(self):
        self.service_a.create(username='staff_a', role=Role.STAFF)
        self.service_b.create(username='staff_b', role=Role.STAFF)
        usernames = set(self.service_a.get_queryset().values_list('username', flat=True))
        self.assertEqual(usernames, {'staff_a'})

    def test_assert_owned_raises_for_cross_school_instance(self):
        other_school_user = self.service_b.create(username='staff_b', role=Role.STAFF)
        with self.assertRaises(TenantMismatchError):
            self.service_a.assert_owned(other_school_user)

    def test_update_refuses_cross_school_instance(self):
        other_school_user = self.service_b.create(username='staff_b', role=Role.STAFF)
        with self.assertRaises(TenantMismatchError):
            self.service_a.update(other_school_user, first_name='Hacked')


class BootstrapSchoolCommandTests(TestCase):
    @override_settings(SINGLE_SCHOOL_MODE=False)
    def test_refuses_to_run_outside_single_school_mode(self):
        with self.assertRaises(CommandError):
            call_command('bootstrap_school', name='Test School', code='TSS001')

    @override_settings(SINGLE_SCHOOL_MODE=True)
    def test_creates_school_and_admin(self):
        call_command(
            'bootstrap_school', name='Test School', code='TSS001',
            admin_username='ssm_admin', admin_password='TestPass123!', stdout=io.StringIO(),
        )
        school = School.objects.get(code='TSS001')
        admin = User.objects.get(username='ssm_admin')
        self.assertEqual(admin.school_id, school.id)
        self.assertEqual(admin.role, Role.SCHOOL_ADMIN)

    @override_settings(SINGLE_SCHOOL_MODE=True)
    def test_running_twice_does_not_duplicate(self):
        call_command('bootstrap_school', name='Test School', code='TSS001', stdout=io.StringIO())
        call_command('bootstrap_school', name='Test School', code='TSS001', stdout=io.StringIO())
        self.assertEqual(School.objects.filter(code='TSS001').count(), 1)


class SeedTestUsersCommandTests(TestCase):
    def test_creates_school_and_one_user_per_role(self):
        call_command('seed_test_users', stdout=io.StringIO())
        self.assertTrue(School.objects.filter(code='DEMO001').exists())
        for username in ('demo_super', 'demo_admin', 'demo_teacher', 'demo_staff'):
            user = User.objects.get(username=username)
            self.assertTrue(user.check_password('Demo@12345'))

    def test_running_twice_does_not_duplicate_school_or_users(self):
        call_command('seed_test_users', stdout=io.StringIO())
        call_command('seed_test_users', stdout=io.StringIO())
        self.assertEqual(School.objects.filter(code='DEMO001').count(), 1)
        self.assertEqual(User.objects.filter(username='demo_admin').count(), 1)

    def test_rerun_restores_password_if_it_drifted(self):
        call_command('seed_test_users', stdout=io.StringIO())
        user = User.objects.get(username='demo_admin')
        user.set_password('SomethingElse123!')
        user.save(update_fields=['password'])

        call_command('seed_test_users', stdout=io.StringIO())

        user.refresh_from_db()
        self.assertTrue(user.check_password('Demo@12345'))
