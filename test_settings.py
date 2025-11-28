# test_settings.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salon_bot.settings')
django.setup()

from django.conf import settings

print("🔧 SETTINGS VERIFICATION")
print("=" * 50)

# Check all critical settings
settings_to_check = [
    ('TELEGRAM_BOT_TOKEN', bool(settings.TELEGRAM_BOT_TOKEN)),
    ('MPESA_CONSUMER_KEY', bool(settings.MPESA_CONSUMER_KEY)),
    ('MPESA_CONSUMER_SECRET', bool(settings.MPESA_CONSUMER_SECRET)),
    ('MPESA_SHORTCODE', bool(settings.MPESA_SHORTCODE)),
    ('MPESA_PASSKEY', bool(settings.MPESA_PASSKEY)),
    ('HUGGINGFACE_API_KEY', bool(settings.HUGGINGFACE_API_KEY)),
    ('DEBUG', settings.DEBUG),
]

print("📋 Configuration Status:")
for setting_name, exists in settings_to_check:
    status = "✅" if exists else "❌"
    print(f"   {status} {setting_name}: {'SET' if exists else 'MISSING'}")

print(f"\n🔑 M-Pesa Shortcode: {settings.MPESA_SHORTCODE}")
print(f"🔑 Consumer Key: {settings.MPESA_CONSUMER_KEY[:15]}...")
print(f"🔑 Passkey Length: {len(settings.MPESA_PASSKEY)}")

print(f"\n🤖 Telegram Token: {'SET' if settings.TELEGRAM_BOT_TOKEN else 'MISSING'}")
print(f"🧠 HuggingFace Key: {'SET' if settings.HUGGINGFACE_API_KEY else 'MISSING'}")