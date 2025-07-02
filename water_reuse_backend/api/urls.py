
# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('home-stats/', views.home_stats, name='home_stats'),
    path('positive-feedback/', views.positive_feedback, name='positive_feedback'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin endpoints
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/water-levels/', views.water_levels, name='water_levels'),
    path('admin/energy-production/', views.energy_production, name='energy_production'),
    path('admin/distribution-monthly/', views.distribution_monthly, name='distribution_monthly'),
    path('admin/pump-status/', views.pump_status, name='pump_status'),
    
    # Client endpoints
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client/add-feedback/', views.add_feedback, name='add_feedback'),
]