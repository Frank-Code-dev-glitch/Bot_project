# bot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # =========================================================================
    # EXISTING PATHS (Keep for backward compatibility)
    # =========================================================================
    path('webhook/', views.telegram_webhook, name='webhook'),  # Now points to telegram_webhook
    path('set_webhook/', views.set_telegram_webhook, name='set_webhook'),  # Now points to set_telegram_webhook
    path('delete_webhook/', views.delete_telegram_webhook, name='delete_webhook'),  # Now points to delete_telegram_webhook
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_bot, name='test_bot'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
    path('test_pay/<str:phone_number>/<int:amount>/', views.test_payment, name='test_payment'),
    
    # =========================================================================
    # NEW WHATSAPP ENDPOINTS
    # =========================================================================
    path('webhook/whatsapp/', views.WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    
    # =========================================================================
    # ADDITIONAL ENHANCED ENDPOINTS (Optional - for better organization)
    # =========================================================================
    path('payment_status/', views.payment_status, name='payment_status'),
    path('service_info/', views.service_info, name='service_info'),
    path('test_payment_flow/', views.test_payment_flow, name='test_payment_flow'),
    
    # =========================================================================
    # PLATFORM-SPECIFIC ALIASES (For clarity)
    # =========================================================================
    path('webhook/telegram/', views.telegram_webhook, name='telegram_webhook'),  # Alias for clarity
    path('set_webhook/telegram/', views.set_telegram_webhook, name='set_telegram_webhook_alias'),  # Alias
    path('delete_webhook/telegram/', views.delete_telegram_webhook, name='delete_telegram_webhook_alias'),  # Alias
]