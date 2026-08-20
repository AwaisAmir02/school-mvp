from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from academics.models import AcademicYear, ClassLevel, Section, Stream
from accounts.choices import Role
from accounts.models import User
from schools.models import School


class AcademicYearConstraintTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')

    def test_only_one_current_academic_year_per_school(self):
        AcademicYear.objects.create(
            school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30', is_current=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AcademicYear.objects.create(
                    school=self.school, name='2026-2027', start_date='2026-06-01', end_date='2027-04-30', is_current=True,
                )

    def test_duplicate_name_within_school_rejected(self):
        AcademicYear.objects.create(school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AcademicYear.objects.create(
                    school=self.school, name='2025-2026', start_date='2025-07-01', end_date='2026-05-30',
                )


class AcademicsTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.class_a = ClassLevel.objects.create(school=self.school_a, name='Grade 1', order=1)
        self.class_b = ClassLevel.objects.create(school=self.school_b, name='Grade 1', order=1)

    def test_for_school_excludes_other_schools_class_levels(self):
        result = ClassLevel.objects.for_school(self.school_a)
        self.assertIn(self.class_a, result)
        self.assertNotIn(self.class_b, result)

    def test_same_class_level_name_allowed_across_different_schools(self):
        self.assertEqual(ClassLevel.objects.filter(name='Grade 1').count(), 2)


class AcademicsViewRBACTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )
        self.teacher_a = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school_a,
        )
        self.class_a = ClassLevel.objects.create(school=self.school_a, name='Grade 1', order=1)
        self.class_b = ClassLevel.objects.create(school=self.school_b, name='Grade 1', order=1)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('academics:class_level_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_school_admin_can_view_class_level_list(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('academics:class_level_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grade 1')

    def test_teacher_denied_manage_academics(self):
        self.client.login(username='teacher_a', password='pass1234')
        response = self.client.get(reverse('academics:class_level_list'))
        self.assertEqual(response.status_code, 403)

    def test_school_admin_cannot_view_other_school_class_level_list_contents(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('academics:class_level_list'))
        self.assertNotIn(self.class_b, response.context['class_levels'])

    def test_school_admin_cannot_edit_other_school_class_level(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('academics:class_level_update', args=[self.class_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_can_create_class_level_for_own_school(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(
            reverse('academics:class_level_create'), {'name': 'Grade 2', 'order': 2},
        )
        self.assertEqual(response.status_code, 302)
        created = ClassLevel.objects.get(name='Grade 2')
        self.assertEqual(created.school_id, self.school_a.id)

    def test_section_form_only_offers_class_levels_from_own_school(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('academics:section_create'))
        form = response.context['form']
        self.assertIn(self.class_a, form.fields['class_level'].queryset)
        self.assertNotIn(self.class_b, form.fields['class_level'].queryset)

    def test_school_admin_cannot_create_section_referencing_other_school_class_level(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.post(
            reverse('academics:section_create'), {'class_level': self.class_b.pk, 'name': 'A'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Section.objects.filter(name='A').exists())


class AcademicsCrossTenantViewAccessTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )
        self.client.login(username='admin_a', password='pass1234')

        self.year_b = AcademicYear.objects.create(
            school=self.school_b, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.stream_b = Stream.objects.create(school=self.school_b, name='Science')
        self.class_b = ClassLevel.objects.create(school=self.school_b, name='Grade 1', order=1)
        self.section_b = Section.objects.create(school=self.school_b, class_level=self.class_b, name='A')

    def test_school_admin_cannot_edit_other_school_academic_year(self):
        response = self.client.get(reverse('academics:academic_year_update', args=[self.year_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_delete_other_school_academic_year(self):
        response = self.client.delete(reverse('academics:academic_year_delete', args=[self.year_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_edit_other_school_stream(self):
        response = self.client.get(reverse('academics:stream_update', args=[self.stream_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_delete_other_school_stream(self):
        response = self.client.delete(reverse('academics:stream_delete', args=[self.stream_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_edit_other_school_section(self):
        response = self.client.get(reverse('academics:section_update', args=[self.section_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_delete_other_school_section(self):
        response = self.client.delete(reverse('academics:section_delete', args=[self.section_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_delete_other_school_class_level(self):
        response = self.client.delete(reverse('academics:class_level_delete', args=[self.class_b.pk]))
        self.assertEqual(response.status_code, 404)
