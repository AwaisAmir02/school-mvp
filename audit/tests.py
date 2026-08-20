from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.choices import Role
from accounts.models import User
from audit.choices import AuditAction
from audit.models import AuditLog
from audit.services import log_action
from audit.tasks import purge_stale_audit_logs
from schools.models import School


class LogActionServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.admin = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school,
        )

    def test_log_action_captures_target_and_school(self):
        log_action(actor=self.admin, action=AuditAction.CREATE, target=self.admin)
        entry = AuditLog.objects.latest('created_at')
        self.assertEqual(entry.action, AuditAction.CREATE)
        self.assertEqual(entry.school_id, self.school.id)
        self.assertEqual(entry.target_type, 'User')

    def test_log_action_handles_none_actor(self):
        log_action(actor=None, action=AuditAction.LOGIN_FAILED, metadata={'username': 'ghost'})
        entry = AuditLog.objects.latest('created_at')
        self.assertIsNone(entry.actor)
        self.assertEqual(entry.metadata['username'], 'ghost')


class LoginAuditSignalTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.user = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school,
        )

    def test_successful_login_is_logged(self):
        self.client.post(reverse('accounts:login'), {'username': 'teacher_a', 'password': 'pass1234'})
        self.assertTrue(AuditLog.objects.filter(action=AuditAction.LOGIN, actor=self.user).exists())

    def test_failed_login_is_logged(self):
        self.client.post(reverse('accounts:login'), {'username': 'teacher_a', 'password': 'wrongpass'})
        self.assertTrue(AuditLog.objects.filter(action=AuditAction.LOGIN_FAILED).exists())


class AuditLogViewTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )
        self.teacher_a = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school_a,
        )
        log_action(actor=self.admin_a, action=AuditAction.UPDATE, target=self.school_a, school=self.school_a)
        log_action(actor=None, action=AuditAction.UPDATE, target=self.school_b, school=self.school_b)

    def test_teacher_denied_audit_log_access(self):
        self.client.login(username='teacher_a', password='pass1234')
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 403)

    def test_school_admin_only_sees_own_school_entries(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('audit:audit_log_list'))
        entries = response.context['audit_logs']
        self.assertTrue(all(entry.school_id == self.school_a.id for entry in entries))
        self.assertTrue(any(entry.action == AuditAction.UPDATE for entry in entries))


class UserAuditIntegrationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.admin = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school,
        )
        self.teacher = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school,
        )
        self.client.login(username='admin_a', password='pass1234')

    def test_role_change_logs_permission_change(self):
        self.client.post(reverse('accounts:user_edit', args=[self.teacher.pk]), {
            'first_name': '', 'last_name': '', 'email': '',
            'role': Role.STAFF, 'phone_number': '', 'is_active': 'on',
        })
        self.assertTrue(
            AuditLog.objects.filter(action=AuditAction.PERMISSION_CHANGE, target_id=str(self.teacher.pk)).exists()
        )

    def test_deactivation_logs_deactivate_action(self):
        self.client.post(reverse('accounts:user_edit', args=[self.teacher.pk]), {
            'first_name': '', 'last_name': '', 'email': '',
            'role': Role.TEACHER, 'phone_number': '',
        })
        self.assertTrue(
            AuditLog.objects.filter(action=AuditAction.DEACTIVATE, target_id=str(self.teacher.pk)).exists()
        )


class PurgeStaleAuditLogsTaskTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')

    def test_purges_only_entries_older_than_retention_window(self):
        old_entry = AuditLog.objects.create(school=self.school, action=AuditAction.LOGIN)
        AuditLog.objects.filter(pk=old_entry.pk).update(created_at=timezone.now() - timedelta(days=400))
        recent_entry = AuditLog.objects.create(school=self.school, action=AuditAction.LOGIN)

        deleted_count = purge_stale_audit_logs()

        self.assertEqual(deleted_count, 1)
        self.assertFalse(AuditLog.objects.filter(pk=old_entry.pk).exists())
        self.assertTrue(AuditLog.objects.filter(pk=recent_entry.pk).exists())
