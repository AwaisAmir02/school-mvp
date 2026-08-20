from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.choices import Role
from accounts.models import User
from schools.models import School


class UserTenantConstraintTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')

    def test_super_admin_must_not_have_school(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username='root', role=Role.SUPER_ADMIN, school=self.school)

    def test_non_super_admin_must_have_school(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username='teacher1', role=Role.TEACHER, school=None)

    def test_create_superuser_sets_role_and_clears_school(self):
        admin_user = User.objects.create_superuser(username='root', password='pass1234')
        self.assertEqual(admin_user.role, Role.SUPER_ADMIN)
        self.assertIsNone(admin_user.school)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)


class UserTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.teacher_a = User.objects.create(username='teacher_a', role=Role.TEACHER, school=self.school_a)
        self.teacher_b = User.objects.create(username='teacher_b', role=Role.TEACHER, school=self.school_b)

    def test_for_school_only_returns_matching_school_users(self):
        school_a_users = User.objects.for_school(self.school_a)
        self.assertIn(self.teacher_a, school_a_users)
        self.assertNotIn(self.teacher_b, school_a_users)

    def test_for_school_is_exhaustive_across_schools(self):
        school_b_users = User.objects.for_school(self.school_b)
        self.assertEqual(list(school_b_users), [self.teacher_b])


class LoginViewTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.user = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school,
        )

    def test_login_succeeds_for_active_school(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'teacher_a', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_blocked_when_school_deactivated(self):
        self.school.is_active = False
        self.school.save()
        response = self.client.post(
            reverse('accounts:login'), {'username': 'teacher_a', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_superuser_redirected_to_django_admin(self):
        User.objects.create_superuser(username='root', password='pass1234')
        response = self.client.post(
            reverse('accounts:login'), {'username': 'root', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:index'))


class UserManagementViewTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )
        self.teacher_a = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school_a,
        )
        self.teacher_b = User.objects.create_user(
            username='teacher_b', password='pass1234', role=Role.TEACHER, school=self.school_b,
        )

    def test_teacher_denied_manage_users(self):
        self.client.login(username='teacher_a', password='pass1234')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_school_admin_user_list_excludes_other_school_users(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertContains(response, 'teacher_a')
        self.assertNotContains(response, 'teacher_b')

    def test_school_admin_cannot_edit_other_school_user(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('accounts:user_edit', args=[self.teacher_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_can_create_user_scoped_to_own_school(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(reverse('accounts:user_create'), {
            'username': 'staff_new',
            'email': 'staff_new@example.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'role': Role.STAFF,
            'phone_number': '',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username='staff_new')
        self.assertEqual(created.school_id, self.school_a.id)
