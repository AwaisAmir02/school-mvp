import io

import openpyxl
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from academics.models import AcademicYear, ClassLevel, Section
from accounts.choices import Role
from accounts.models import User
from audit.choices import AuditAction
from audit.models import AuditLog
from schools.models import School
from students.imports import StudentImportError, import_students
from students.models import Student


def _build_workbook(rows, columns=None):
    columns = columns or [
        'admission_number', 'first_name', 'last_name', 'date_of_birth', 'gender',
        'class_level', 'section', 'guardian_name', 'guardian_phone', 'email',
    ]
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(columns)
    for row in rows:
        sheet.append([row.get(column, '') for column in columns])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    buffer.name = 'students.xlsx'
    return buffer


class StudentConstraintTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.academic_year = AcademicYear.objects.create(
            school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name='Grade 1', order=1)

    def test_duplicate_admission_number_within_school_rejected(self):
        Student.objects.create(
            school=self.school, admission_number='ADM001', first_name='Amir', last_name='Khan',
            academic_year=self.academic_year, class_level=self.class_level,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Student.objects.create(
                    school=self.school, admission_number='ADM001', first_name='Sara', last_name='Ali',
                    academic_year=self.academic_year, class_level=self.class_level,
                )


class StudentTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='Green Valley High', code='GVH001')
        self.school_b = School.objects.create(name='Riverside Academy', code='RVA001')
        self.year_a = AcademicYear.objects.create(
            school=self.school_a, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.year_b = AcademicYear.objects.create(
            school=self.school_b, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.class_a = ClassLevel.objects.create(school=self.school_a, name='Grade 1', order=1)
        self.class_b = ClassLevel.objects.create(school=self.school_b, name='Grade 1', order=1)
        self.student_a = Student.objects.create(
            school=self.school_a, admission_number='ADM001', first_name='Amir', last_name='Khan',
            academic_year=self.year_a, class_level=self.class_a,
        )
        self.student_b = Student.objects.create(
            school=self.school_b, admission_number='ADM001', first_name='Sara', last_name='Ali',
            academic_year=self.year_b, class_level=self.class_b,
        )
        self.admin_a = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school_a,
        )

    def test_same_admission_number_allowed_across_different_schools(self):
        self.assertEqual(Student.objects.filter(admission_number='ADM001').count(), 2)

    def test_for_school_excludes_other_schools_students(self):
        result = Student.objects.for_school(self.school_a)
        self.assertIn(self.student_a, result)
        self.assertNotIn(self.student_b, result)

    def test_school_admin_cannot_view_other_school_student(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('students:student_update', args=[self.student_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_delete_other_school_student(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.delete(reverse('students:student_delete', args=[self.student_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Student.objects.filter(pk=self.student_b.pk).exists())

    def test_school_admin_student_list_excludes_other_school(self):
        self.client.login(username='admin_a', password='pass1234')
        response = self.client.get(reverse('students:student_list'))
        self.assertContains(response, 'ADM001')
        self.assertNotContains(response, 'Sara')


class StudentViewRBACTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.teacher = User.objects.create_user(
            username='teacher_a', password='pass1234', role=Role.TEACHER, school=self.school,
        )
        self.staff_role = User.objects.create_user(
            username='staff_a', password='pass1234', role=Role.STAFF, school=self.school,
        )

    def test_teacher_can_manage_students(self):
        self.client.login(username='teacher_a', password='pass1234')
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_role_denied_manage_students(self):
        self.client.login(username='staff_a', password='pass1234')
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 403)


class StudentImportServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.academic_year = AcademicYear.objects.create(
            school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name='Grade 1', order=1)
        self.section = Section.objects.create(school=self.school, class_level=self.class_level, name='A')

    def test_missing_required_columns_raises(self):
        workbook = _build_workbook([], columns=['first_name', 'last_name'])
        with self.assertRaises(StudentImportError):
            import_students(file=workbook, school=self.school, academic_year=self.academic_year)

    def test_valid_row_creates_student(self):
        workbook = _build_workbook([{
            'admission_number': 'ADM001', 'first_name': 'Amir', 'last_name': 'Khan',
            'class_level': 'Grade 1', 'section': 'A',
        }])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.created_count, 1)
        self.assertEqual(summary.error_count, 0)
        student = Student.objects.get(admission_number='ADM001')
        self.assertEqual(student.class_level_id, self.class_level.id)
        self.assertEqual(student.section_id, self.section.id)

    def test_missing_required_field_reported_as_row_error(self):
        workbook = _build_workbook([{
            'admission_number': '', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 1',
        }])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.created_count, 0)
        self.assertEqual(summary.error_count, 1)
        self.assertIn('Admission number is required.', summary.row_results[0].errors)

    def test_unknown_class_level_reported_as_row_error(self):
        workbook = _build_workbook([{
            'admission_number': 'ADM002', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 99',
        }])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.error_count, 1)
        self.assertTrue(any('does not exist' in error for error in summary.row_results[0].errors))

    def test_duplicate_admission_number_within_file_reported(self):
        workbook = _build_workbook([
            {'admission_number': 'ADM003', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 1'},
            {'admission_number': 'ADM003', 'first_name': 'Sara', 'last_name': 'Ali', 'class_level': 'Grade 1'},
        ])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.created_count, 1)
        self.assertEqual(summary.error_count, 1)

    def test_duplicate_against_existing_student_reported(self):
        Student.objects.create(
            school=self.school, admission_number='ADM004', first_name='Existing', last_name='Student',
            academic_year=self.academic_year, class_level=self.class_level,
        )
        workbook = _build_workbook([{
            'admission_number': 'ADM004', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 1',
        }])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.created_count, 0)
        self.assertEqual(summary.error_count, 1)

    def test_import_is_scoped_to_school_class_levels(self):
        other_school = School.objects.create(name='Riverside Academy', code='RVA001')
        ClassLevel.objects.create(school=other_school, name='Grade 5', order=1)
        workbook = _build_workbook([{
            'admission_number': 'ADM005', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 5',
        }])
        summary = import_students(file=workbook, school=self.school, academic_year=self.academic_year)
        self.assertEqual(summary.error_count, 1)


class StudentImportViewTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.academic_year = AcademicYear.objects.create(
            school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name='Grade 1', order=1)
        self.admin = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school,
        )

    def test_import_view_creates_students_and_shows_summary(self):
        self.client.login(username='admin_a', password='pass1234')
        workbook = _build_workbook([{
            'admission_number': 'ADM010', 'first_name': 'Amir', 'last_name': 'Khan', 'class_level': 'Grade 1',
        }])
        response = self.client.post(reverse('students:student_import'), {
            'academic_year': self.academic_year.pk,
            'file': workbook,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ADM010')
        self.assertTrue(Student.objects.filter(admission_number='ADM010').exists())


class StudentAuditIntegrationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley High', code='GVH001')
        self.academic_year = AcademicYear.objects.create(
            school=self.school, name='2025-2026', start_date='2025-06-01', end_date='2026-04-30',
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name='Grade 1', order=1)
        self.section = Section.objects.create(school=self.school, class_level=self.class_level, name='A')
        self.admin = User.objects.create_user(
            username='admin_a', password='pass1234', role=Role.SCHOOL_ADMIN, school=self.school,
        )
        self.client.login(username='admin_a', password='pass1234')

    def test_create_logs_audit_action(self):
        self.client.post(reverse('students:student_create'), {
            'admission_number': 'ADM020', 'first_name': 'Amir', 'last_name': 'Khan',
            'academic_year': self.academic_year.pk, 'class_level': self.class_level.pk,
            'section': self.section.pk, 'guardian_name': '', 'guardian_phone': '', 'email': '',
        })
        student = Student.objects.get(admission_number='ADM020')
        self.assertTrue(
            AuditLog.objects.filter(action=AuditAction.CREATE, target_type='Student', target_id=str(student.pk)).exists()
        )

    def test_delete_logs_audit_action_with_identifying_metadata(self):
        student = Student.objects.create(
            school=self.school, admission_number='ADM021', first_name='Amir', last_name='Khan',
            academic_year=self.academic_year, class_level=self.class_level, section=self.section,
        )
        self.client.delete(reverse('students:student_delete', args=[student.pk]))
        entry = AuditLog.objects.get(action=AuditAction.DELETE, target_type='Student', target_id=str(student.pk))
        self.assertEqual(entry.metadata['admission_number'], 'ADM021')
        self.assertEqual(entry.metadata['class_level'], 'Grade 1')
        self.assertEqual(entry.metadata['section'], 'A')
