# railway_bot.py
import os
import django
import time
import logging

# Clear proxy settings
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salon_bot.settings')
django.setup()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for Railway deployment"""
    print("🚀 Starting Salon Bot on Railway...")
    print("🔧 Environment:", os.environ.get('RAILWAY_ENVIRONMENT', 'production'))
    
    # Import and run your bot
    from working_booking_bot import run_working_booking_bot
    
    # Run with retry logic for Railway
    max_retries = 3
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Starting bot (attempt {attempt + 1}/{max_retries})...")
            run_working_booking_bot()
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("🔴 Max retries reached. Bot stopped.")
                raise

if __name__ == '__main__':
    main()