from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.choices import Role
from accounts.models import User
from schools.models import School
from staff.models import Staff
from staff.services import StaffActivationError, activate_staff, deactivate_staff, reactivate_staff


class StaffConstraintTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')

    def test_duplicate_employee_code_within_school_rejected(self):
        Staff.objects.create(
            school=self.school, employee_code='EMP001', first_name='Ada', last_name='Lovelace',
            designation='Math Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Staff.objects.create(
                    school=self.school, employee_code='EMP001', first_name='Grace', last_name='Hopper',
                    designation='Science Teacher', role=Role.TEACHER, date_joined='2025-06-01',
                )


class StaffActivationServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.staff_member = Staff.objects.create(
            school=self.school, employee_code='EMP001', first_name='Ada', last_name='Lovelace',
            designation='Math Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )

    def test_activate_creates_linked_user_with_matching_school_and_role(self):
        user = activate_staff(self.staff_member, username='ada.lovelace', password='pass1234')
        self.staff_member.refresh_from_db()
        self.assertEqual(self.staff_member.user_id, user.id)
        self.assertEqual(user.school_id, self.school.id)
        self.assertEqual(user.role, Role.TEACHER)
        self.assertTrue(user.is_active)

    def test_activate_twice_raises(self):
        activate_staff(self.staff_member, username='ada.lovelace', password='pass1234')
        with self.assertRaises(StaffActivationError):
            activate_staff(self.staff_member, username='ada.lovelace2', password='pass1234')

    def test_deactivate_disables_linked_user_login(self):
        activate_staff(self.staff_member, username='ada.lovelace', password='pass1234')
        deactivate_staff(self.staff_member)
        self.staff_member.refresh_from_db()
        self.assertFalse(self.staff_member.is_active)
        self.assertFalse(self.staff_member.user.is_active)

    def test_reactivate_restores_linked_user_login(self):
        activate_staff(self.staff_member, username='ada.lovelace', password='pass1234')
        deactivate_staff(self.staff_member)
        reactivate_staff(self.staff_member)
        self.staff_member.refresh_from_db()
        self.assertTrue(self.staff_member.is_active)
        self.assertTrue(self.staff_member.user.is_active)


class StaffTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.staff_a = Staff.objects.create(
            school=self.school_a, employee_code='EMP001', first_name='Ada', last_name='Lovelace',
            designation='Math Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )
        self.staff_b = Staff.objects.create(
            school=self.school_b, employee_code='EMP001', first_name='Grace', last_name='Hopper',
            designation='Science Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )

    def test_for_school_excludes_other_schools_staff(self):
        result = Staff.objects.for_school(self.school_a)
        self.assertIn(self.staff_a, result)
        self.assertNotIn(self.staff_b, result)


class StaffViewRBACAndTenantTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )
        self.staff_role_user_a = User.objects.create_user(
            username='staff_a', password='pass1234', role=Role.STAFF, school=self.school_a,
        )
        self.staff_a = Staff.objects.create(
            school=self.school_a, employee_code='EMP001', first_name='Ada', last_name='Lovelace',
            designation='Math Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )
        self.staff_b = Staff.objects.create(
            school=self.school_b, employee_code='EMP001', first_name='Grace', last_name='Hopper',
            designation='Science Teacher', role=Role.TEACHER, date_joined='2025-06-01',
        )

    def test_staff_role_user_denied_manage_staff(self):
        self.client.login(username='staff_a', password='pass1234')
        response = self.client.get(reverse('staff:staff_list'))
        self.assertEqual(response.status_code, 403)

    def test_school_admin_cannot_edit_other_school_staff(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('staff:staff_update', args=[self.staff_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_activate_other_school_staff(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(
            reverse('staff:staff_activate', args=[self.staff_b.pk]),
            {'username': 'grace.hopper', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, 404)
        self.staff_b.refresh_from_db()
        self.assertFalse(self.staff_b.is_activated)

    def test_school_admin_can_activate_own_school_staff(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(
            reverse('staff:staff_activate', args=[self.staff_a.pk]),
            {'username': 'ada.lovelace', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, 302)
        self.staff_a.refresh_from_db()
        self.assertTrue(self.staff_a.is_activated)
        self.assertEqual(self.staff_a.user.school_id, self.school_a.id)

    def test_school_admin_cannot_toggle_active_other_school_staff(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(reverse('staff:staff_toggle_active', args=[self.staff_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.staff_b.refresh_from_db()
        self.assertTrue(self.staff_b.is_active)

    def test_school_admin_cannot_view_other_school_staff_in_list(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('staff:staff_list'))
        self.assertNotIn(self.staff_b, response.context['staff_members'])
