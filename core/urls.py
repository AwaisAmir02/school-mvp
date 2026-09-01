import os

from decouple import config
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView


def debug_static_check(request):
    static_root = str(settings.STATIC_ROOT)
    static_root_exists = os.path.exists(settings.STATIC_ROOT)
    base_dir = str(settings.BASE_DIR)
    base_dir_exists = os.path.exists(settings.BASE_DIR)
    data = {
        'STATIC_ROOT': static_root,
        'static_root_exists': static_root_exists,
        'static_root_is_dir': os.path.isdir(settings.STATIC_ROOT),
        'BASE_DIR': base_dir,
        'base_dir_exists': base_dir_exists,
    }
    if static_root_exists:
        data['static_root_listdir'] = os.listdir(settings.STATIC_ROOT)[:20]
    if base_dir_exists:
        data['base_dir_listdir'] = os.listdir(settings.BASE_DIR)[:20]
    return JsonResponse(data)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='schools:dashboard', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('', include('schools.urls')),
    path('academics/', include('academics.urls')),
    path('staff/', include('staff.urls')),
    path('students/', include('students.urls')),
    path('audit/', include('audit.urls')),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if config('DEBUG_STATIC_CHECK', default=False, cast=bool):
    urlpatterns += [path('debug-static-check/', debug_static_check)]
