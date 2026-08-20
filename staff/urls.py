from django.urls import path

from staff import views

app_name = 'staff'

urlpatterns = [
    path('', views.StaffListView.as_view(), name='staff_list'),
    path('create/', views.StaffCreateView.as_view(), name='staff_create'),
    path('<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('<int:pk>/activate/', views.StaffActivateView.as_view(), name='staff_activate'),
    path('<int:pk>/toggle-active/', views.StaffToggleActiveView.as_view(), name='staff_toggle_active'),
]
