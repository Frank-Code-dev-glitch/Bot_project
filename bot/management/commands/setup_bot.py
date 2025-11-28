# bot/management/commands/setup_bot.py
from django.core.management.base import BaseCommand
from bot.services.telegram_service import TelegramService

class Command(BaseCommand):
    help = 'Setup Telegram bot webhook'

    def handle(self, *args, **options):
        self.stdout.write("🤖 Setting up Telegram bot...")
        
        try:
            # Set webhook
            telegram = TelegramService()
            result = telegram.set_webhook()
            
            self.stdout.write(f"📡 Webhook response: {result}")
            
            # Proper response handling
            if isinstance(result, dict):
                if result.get('ok'):
                    self.stdout.write(
                        self.style.SUCCESS('✅ Webhook is set and working!')
                    )
                    description = result.get('description', 'Webhook configured')
                    self.stdout.write(f'📝 Status: {description}')
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Webhook setup had issues')
                    )
                    error_desc = result.get('description', 'Unknown error')
                    self.stdout.write(f'❌ Error: {error_desc}')
            else:
                # If result is not a dictionary (shouldn't happen with our service)
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook setup completed!')
                )
                
            # Test bot connectivity
            self.test_bot_info()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )

    def test_bot_info(self):
        """Test if we can get bot information from Telegram"""
        try:
            from bot.services.telegram_service import TelegramService
            telegram = TelegramService()
            
            import requests
            response = requests.get(f"{telegram.base_url}/getMe")
            
            if response.status_code == 200:
                bot_data = response.json()
                if bot_data.get('ok'):
                    bot_info = bot_data['result']
                    self.stdout.write("\n🤖 Bot Information:")
                    self.stdout.write(f"   Name: {bot_info['first_name']}")
                    self.stdout.write(f"   Username: @{bot_info['username']}")
                    self.stdout.write(f"   ID: {bot_info['id']}")
                    self.stdout.write(self.style.SUCCESS('   ✅ Bot is connected!'))
                else:
                    self.stdout.write(self.style.ERROR('   ❌ Cannot fetch bot info'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Failed to connect to Telegram API'))
                
        except Exception as e:
            self.stdout.write(f'   ⚠️ Bot info test failed: {e}')