# salon_bot/urls.py - Updated
from django.contrib import admin
from django.urls import path, include
from bot.views import WhatsAppWebhookView, HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bot/', include('bot.urls')),
    
    # WhatsApp Webhook endpoints
    path('webhook/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
]