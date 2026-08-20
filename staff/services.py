from django.db import transaction

from accounts.models import User


class StaffActivationError(Exception):
    pass


@transaction.atomic
def activate_staff(staff, username, password):
    if staff.user_id is not None:
        raise StaffActivationError('This staff member is already activated.')
    user = User.objects.create_user(
        username=username,
        password=password,
        school=staff.school,
        role=staff.role,
        first_name=staff.first_name,
        last_name=staff.last_name,
        email=staff.email,
        phone_number=staff.phone_number,
    )
    staff.user = user
    staff.save(update_fields=['user'])
    return user


@transaction.atomic
def deactivate_staff(staff):
    staff.is_active = False
    staff.save(update_fields=['is_active'])
    if staff.user_id:
        staff.user.is_active = False
        staff.user.save(update_fields=['is_active'])


@transaction.atomic
def reactivate_staff(staff):
    staff.is_active = True
    staff.save(update_fields=['is_active'])
    if staff.user_id:
        staff.user.is_active = True
        staff.user.save(update_fields=['is_active'])
