from django.urls import path
from . import views

urlpatterns = [
    # Telegram endpoints
    path('webhook/telegram/', views.telegram_webhook, name='telegram_webhook'),
    path('set-webhook/telegram/', views.set_telegram_webhook, name='set_telegram_webhook'),
    path('delete-webhook/telegram/', views.delete_telegram_webhook, name='delete_telegram_webhook'),
    
    # WhatsApp endpoints
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
    
    # Health & Testing
    path('health/', views.health_check, name='health_check'),
    path('test-bot/', views.test_bot, name='test_bot'),
    path('test-payment/', views.test_payment, name='test_payment'),
    path('test-payment-flow/', views.test_payment_flow, name='test_payment_flow'),
    
    # M-Pesa & Payment
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('payment/status/', views.payment_status, name='payment_status'),
    path('service/info/', views.service_info, name='service_info'),
]
