# salon_bot/urls.py - UPDATED & CORRECTED
from django.contrib import admin
from django.urls import path, include
from bot.views import health_check  # ✅ Import the function directly

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include all bot URLs from bot/urls.py
    path('', include('bot.urls')),  # ✅ This includes ALL your bot URLs at root level
    
    # Health check (keep this if you want it at root)
    path('health/', health_check, name='health_check'),
]
