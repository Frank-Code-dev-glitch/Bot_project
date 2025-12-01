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

# Import only what actually exists
from .whatsapp_views import whatsapp_webhook

# Try to import optional functions
try:
    from .whatsapp_views import whatsapp_health_check
except ImportError:
    whatsapp_health_check = None

try:
    from .whatsapp_views import WhatsAppWebhookView
except ImportError:
    WhatsAppWebhookView = None

# Export all views (only what exists)
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
]

# Add optional imports only if they exist
if whatsapp_health_check:
    __all__.append('whatsapp_health_check')
    
if WhatsAppWebhookView:
    __all__.append('WhatsAppWebhookView')