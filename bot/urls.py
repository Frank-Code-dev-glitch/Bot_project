# bot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('set_webhook/', views.set_webhook_view, name='set_webhook'),
    path('delete_webhook/', views.delete_webhook_view, name='delete_webhook'),
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_bot, name='test_bot'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
    path('test_pay/<str:phone_number>/<int:amount>/', views.test_payment, name='test_payment'),
]