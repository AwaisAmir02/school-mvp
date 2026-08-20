from django import template

register = template.Library()

APP_ICONS = {
    'academics': 'ri-calendar-2-line',
    'accounts': 'ri-user-settings-line',
    'audit': 'ri-history-line',
    'auth': 'ri-shield-user-line',
    'django_celery_beat': 'ri-time-line',
    'schools': 'ri-building-4-line',
    'staff': 'ri-team-line',
    'students': 'ri-graduation-cap-line',
}

DEFAULT_APP_ICON = 'ri-apps-2-line'


@register.filter
def admin_app_icon(app_label):
    return APP_ICONS.get(app_label, DEFAULT_APP_ICON)
