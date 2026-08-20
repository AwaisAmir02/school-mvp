from django.urls import path

from schools import views

app_name = 'schools'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.SchoolProfileUpdateView.as_view(), name='profile'),

    path('super/dashboard/', views.SuperAdminDashboardView.as_view(), name='super_dashboard'),
    path('super/schools/', views.SchoolListView.as_view(), name='school_list'),
    path('super/schools/create/', views.SchoolCreateView.as_view(), name='school_create'),
    path('super/schools/<int:pk>/edit/', views.SchoolUpdateView.as_view(), name='school_update'),
    path('super/schools/<int:pk>/toggle-active/', views.SchoolToggleActiveView.as_view(), name='school_toggle_active'),
]
