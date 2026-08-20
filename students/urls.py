from django.urls import path

from students import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('import/', views.StudentImportView.as_view(), name='student_import'),
    path('import/template/', views.StudentImportTemplateView.as_view(), name='student_import_template'),
]
