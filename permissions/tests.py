from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.choices import Role
from accounts.models import User
from permissions.constants import Perm
from permissions.registry import role_has_permission, user_has_permission
from schools.models import School


class RolePermissionRegistryTests(TestCase):
    def test_school_admin_can_manage_school_profile(self):
        self.assertTrue(role_has_permission(Role.SCHOOL_ADMIN, Perm.MANAGE_SCHOOL_PROFILE))

    def test_teacher_cannot_manage_school_profile(self):
        self.assertFalse(role_has_permission(Role.TEACHER, Perm.MANAGE_SCHOOL_PROFILE))

    def test_staff_cannot_manage_users(self):
        self.assertFalse(role_has_permission(Role.STAFF, Perm.MANAGE_USERS))

    def test_teacher_can_manage_students(self):
        self.assertTrue(role_has_permission(Role.TEACHER, Perm.MANAGE_STUDENTS))

    def test_super_admin_can_manage_schools(self):
        self.assertTrue(role_has_permission(Role.SUPER_ADMIN, Perm.MANAGE_SCHOOLS))

    def test_school_admin_cannot_manage_schools(self):
        self.assertFalse(role_has_permission(Role.SCHOOL_ADMIN, Perm.MANAGE_SCHOOLS))

    def test_teacher_cannot_manage_schools(self):
        self.assertFalse(role_has_permission(Role.TEACHER, Perm.MANAGE_SCHOOLS))

    def test_staff_cannot_manage_schools(self):
        self.assertFalse(role_has_permission(Role.STAFF, Perm.MANAGE_SCHOOLS))


class UserPermissionTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')

    def test_anonymous_user_has_no_permissions(self):
        self.assertFalse(user_has_permission(AnonymousUser(), Perm.VIEW_DASHBOARD))

    def test_superuser_has_every_permission_regardless_of_role(self):
        superuser = User.objects.create_superuser(username='root', password='pass1234')
        self.assertTrue(user_has_permission(superuser, Perm.MANAGE_STAFF))
        self.assertTrue(user_has_permission(superuser, Perm.MANAGE_STUDENTS))

    def test_school_admin_user_has_manage_permissions(self):
        admin_user = User.objects.create_user(
            username='school_admin', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school,
        )
        self.assertTrue(user_has_permission(admin_user, Perm.MANAGE_STAFF))

    def test_staff_user_lacks_manage_permissions(self):
        staff_user = User.objects.create_user(
            username='staff_member', password='pass1234', role=Role.STAFF, school=self.school,
        )
        self.assertFalse(user_has_permission(staff_user, Perm.MANAGE_STAFF))
        self.assertFalse(user_has_permission(staff_user, Perm.MANAGE_USERS))
