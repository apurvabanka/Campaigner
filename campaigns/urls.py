from django.urls import path
from . import views

urlpatterns = [
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('create_campaign_ajax/', views.create_campaign_ajax, name='create_campaign_ajax'),
    path('campaign_list/', views.campaign_list, name='campaign_list'),
    path('refer_customer/<str:referral_code>/', views.refer_customer, name='refer_customer'),
    path('assign_customer/<int:campaign_id>/', views.assign_customer, name='assign_customer'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('onboard/', views.onboarding, name='onboard'),
    path('thank_you/', views.thank_you, name='thank_you'),
]