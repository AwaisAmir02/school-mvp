from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone


def _month_start(value, months_ago):
    month_index = value.month - 1 - months_ago
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1)


def _monthly_counts(queryset, date_field, months=6):
    today = timezone.localdate().replace(day=1)
    earliest = _month_start(today, months - 1)
    raw_counts = (
        queryset.filter(**{f'{date_field}__date__gte': earliest})
        .annotate(month=TruncMonth(date_field))
        .values('month')
        .annotate(total=Count('pk'))
    )
    counts_by_key = {(row['month'].year, row['month'].month): row['total'] for row in raw_counts}
    series = []
    for offset in range(months - 1, -1, -1):
        month = _month_start(today, offset)
        series.append({'label': month.strftime('%b'), 'count': counts_by_key.get((month.year, month.month), 0)})
    return series


def _sparkline(series, bar_width=14, gap=6, height=28):
    max_count = max((point['count'] for point in series), default=0) or 1
    bars = []
    for index, point in enumerate(series):
        bar_height = round((point['count'] / max_count) * height) if point['count'] else 0
        bars.append({
            'label': point['label'],
            'count': point['count'],
            'x': index * (bar_width + gap),
            'y': height - bar_height,
            'height': bar_height,
        })
    width = len(series) * (bar_width + gap) - gap if series else 0
    return {'bars': bars, 'width': width, 'height': height, 'bar_width': bar_width}


class SchoolMVPAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        context = dict(extra_context or {})
        if request.user.is_authenticated and request.user.is_superuser:
            from accounts.models import User
            from schools.models import School
            from students.models import Student

            context.update({
                'dashboard_school_count': School.objects.count(),
                'dashboard_active_school_count': School.objects.filter(is_active=True).count(),
                'dashboard_user_count': User.objects.count(),
                'dashboard_student_count': Student.objects.count(),
                'dashboard_school_sparkline': _sparkline(_monthly_counts(School.objects.all(), 'created_at')),
                'dashboard_user_sparkline': _sparkline(_monthly_counts(User.objects.all(), 'date_joined')),
            })
        return super().index(request, extra_context=context)


class SchoolMVPAdminConfig(AdminConfig):
    default_site = 'common.admin.SchoolMVPAdminSite'
