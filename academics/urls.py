from django.urls import path

from academics import views

app_name = 'academics'

urlpatterns = [
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('academic-years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),
    path('academic-years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),

    path('class-levels/', views.ClassLevelListView.as_view(), name='class_level_list'),
    path('class-levels/create/', views.ClassLevelCreateView.as_view(), name='class_level_create'),
    path('class-levels/<int:pk>/edit/', views.ClassLevelUpdateView.as_view(), name='class_level_update'),
    path('class-levels/<int:pk>/delete/', views.ClassLevelDeleteView.as_view(), name='class_level_delete'),

    path('streams/', views.StreamListView.as_view(), name='stream_list'),
    path('streams/create/', views.StreamCreateView.as_view(), name='stream_create'),
    path('streams/<int:pk>/edit/', views.StreamUpdateView.as_view(), name='stream_update'),
    path('streams/<int:pk>/delete/', views.StreamDeleteView.as_view(), name='stream_delete'),

    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_update'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),

    path('section-options/', views.SectionOptionsView.as_view(), name='section_options'),
]
