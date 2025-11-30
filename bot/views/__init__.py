# bot/views/__init__.py
from .telegram_views import (
    telegram_webhook,
    set_telegram_webhook, 
    delete_telegram_webhook,
    health_check,
    test_bot,
    mpesa_callback,
    test_payment,
    payment_status,
    service_info,
    test_payment_flow
)

from .whatsapp_views import (
    whatsapp_webhook,
    whatsapp_health_check,
    WhatsAppWebhookView
)

# Export all views
__all__ = [
    'telegram_webhook',
    'set_telegram_webhook',
    'delete_telegram_webhook', 
    'health_check',
    'test_bot',
    'mpesa_callback',
    'test_payment',
    'payment_status',
    'service_info',
    'test_payment_flow',
    'whatsapp_webhook',
    'whatsapp_health_check',
    'WhatsAppWebhookView'
]