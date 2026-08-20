from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

admin.site.site_header = 'School MVP Administration'
admin.site.site_title = 'School MVP'
admin.site.index_title = 'Site Administration'

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
