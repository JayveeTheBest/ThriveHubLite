from django.urls import path
from . import views

urlpatterns = [
    path('log-call/', views.log_call, name='log_call'),
    path('generate-summary/', views.generate_summary, name='generate_summary'),
    path('logs/', views.call_logs, name='call_logs'),
]