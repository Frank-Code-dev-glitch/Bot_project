# salon_bot/urls.py - CORRECTED
from django.contrib import admin
from django.urls import path, include
from bot.views import WhatsAppWebhookView, health_check  # ✅ Use function-based health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bot/', include('bot.urls')),
    
    # WhatsApp Webhook endpoints
    path('webhook/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('health/', health_check, name='health_check'),  # ✅ Function-based, not class-based
]