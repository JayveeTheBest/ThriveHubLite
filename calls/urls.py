from django.urls import path
from . import views

urlpatterns = [
    path('log-call/', views.log_call, name='log_call'),
    path('generate-summary/', views.generate_summary, name='generate_summary'),
    path('logs/', views.call_logs, name='call_logs'),
    path('referrals/', views.referrals, name='referrals'),
    path('add/', views.add_referral, name='add_referral'),
    path('referral/edit/<int:pk>/', views.edit_referral, name='edit_referral'),
    path('referral/delete/<int:pk>/', views.delete_referral, name='delete_referral'),
    path('referral/<int:id>/', views.referral_detail, name='referral_detail'),
]