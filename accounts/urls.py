from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_customer/', views.add_customer, name='add_customer'),
    path('bulk_upload_customers/', views.bulk_upload_customers, name='bulk_upload_customers'),
    path('', views.register_or_login, name='register_or_login'),
    path('logout/', views.user_logout, name='logout'),
]