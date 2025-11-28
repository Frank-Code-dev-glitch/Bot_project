# working_booking_bot.py
import os
import sys
import time
import requests
import logging
from datetime import datetime

# 🧹 Clear all proxy settings
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(var, None)

print("🧹 All proxy environment variables cleared")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salon_bot.settings')

import django
django.setup()

from django.conf import settings
from bot.services.mpesa_service import MpesaService

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class NetworkResilientTelegramClient:
    """Telegram client with Railway-optimized network handling"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Enhanced session for Railway
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.proxies.clear()
        
        # Add retry strategy
        from requests.adapters import HTTPAdapter, Retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        print("🔧 Railway-optimized connection configured")
    
    def test_connection(self):
        """Test Telegram API connection with detailed diagnostics"""
        try:
            print("🔌 Testing Telegram connection...")
            response = self.session.get(f"{self.base_url}/getMe", timeout=15)
            
            if response.status_code == 200:
                bot_info = response.json()['result']
                print(f"✅ Connected to: {bot_info['first_name']} (@{bot_info['username']})")
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_updates(self, offset=None, timeout=10, limit=100):
        """Get updates with Railway-optimized timeouts"""
        try:
            params = {'timeout': timeout, 'limit': limit}
            if offset:
                params['offset'] = offset
                
            response = self.session.get(
                f"{self.base_url}/getUpdates", 
                params=params, 
                timeout=timeout + 5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except requests.exceptions.Timeout:
            return {'ok': True, 'result': []}
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return None
    
    def send_message(self, chat_id, text, parse_mode='Markdown', reply_markup=None):
        """Send message with enhanced error handling"""
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = reply_markup
                
            response = self.session.post(f"{self.base_url}/sendMessage", json=payload, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {chat_id}")
            else:
                logger.error(f"❌ Failed to send message: {response.status_code}")
                
            return response.json()
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return None
    
    def send_message_with_buttons(self, chat_id, text, buttons):
        """Send message with inline keyboard"""
        keyboard = {'inline_keyboard': buttons}
        return self.send_message(chat_id, text, reply_markup=keyboard)
    
    def answer_callback_query(self, callback_query_id, text=None):
        """Answer callback query"""
        try:
            payload = {'callback_query_id': callback_query_id}
            if text:
                payload['text'] = text
                
            response = self.session.post(f"{self.base_url}/answerCallbackQuery", json=payload, timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"❌ Error answering callback: {e}")
            return None

class WorkingBookingBot:
    """Booking bot optimized for Railway deployment"""
    
    def __init__(self, telegram_client):
        self.telegram = telegram_client
        self.mpesa_service = MpesaService()
        self.user_states = {}
        self.last_mpesa_status = None
        self.status_check_time = None
        
        logger.info("✅ WorkingBookingBot initialized for Railway")
    
    def handle_update(self, update):
        """Handle all updates with Railway-optimized error handling"""
        try:
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
        except Exception as e:
            logger.error(f"Error handling update: {e}")
    
    def handle_message(self, message):
        """Handle incoming messages"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        
        logger.info(f"📨 Message from {chat_id}: {text}")
        
        if text.startswith('/'):
            self.handle_command(chat_id, text)
        else:
            user_state = self.user_states.get(chat_id, {})
            
            if user_state.get('state') == 'awaiting_service':
                self.handle_service_selection(chat_id, text)
            elif user_state.get('state') == 'awaiting_phone':
                self.handle_phone_input(chat_id, text)
            else:
                self.handle_regular_message(chat_id, text)
    
    def handle_command(self, chat_id, text):
        """Handle bot commands"""
        command = text.lower().strip()
        
        if command == '/start':
            self.send_welcome_message(chat_id)
        elif command == '/book':
            self.start_booking_flow(chat_id)
        elif command == '/services':
            self.show_services(chat_id)
        elif command == '/prices':
            self.show_prices(chat_id)
        elif command == '/status':
            self.check_mpesa_status(chat_id)
        elif command == '/help':
            self.show_help(chat_id)
        else:
            self.telegram.send_message(chat_id, "❌ Unknown command. Try /start for available commands.")
    
    def send_welcome_message(self, chat_id):
        """Send welcome message optimized for mobile"""
        response = """
👋 *Welcome to Frank Beauty Spot!* 💅

I'm your personal booking assistant! 

💬 *Quick Commands:*
/book - Book an appointment  
/services - See services & prices
/status - Check payment status
/help - Get help

💡 *Or just type:* "I want to book a haircut"

Let's get you booked in! 😊
        """
        self.telegram.send_message(chat_id, response)
    
    def show_help(self, chat_id):
        """Show help message"""
        response = """
🆘 *Help Guide*

*Booking Flow:*
1. Send /book or type "book appointment"
2. Tell me the service you want
3. Choose payment method
4. Complete payment

*Payment Methods:*
• M-Pesa STK Push (automatic)
• Manual M-Pesa 
• Cash at salon

*Need Help?*
Contact support if you have any issues!
        """
        self.telegram.send_message(chat_id, response)
    
    def start_booking_flow(self, chat_id):
        """Start the booking process"""
        response = """
🎉 *Let's Book Your Appointment!* 

What service would you like? You can say:

💇 *Hair Services:*
• Haircut / Trim
• Hair Color / Dye

💅 *Nail Services:*
• Manicure / Nails
• Pedicure

✨ *Other Services:*
• Facial / Skincare
• Makeup

Tell me what service you'd like! 💅
        """
        self.telegram.send_message(chat_id, response)
        self.user_states[chat_id] = {'state': 'awaiting_service'}
        logger.info(f"✅ Started booking flow for {chat_id}")
    
    def handle_service_selection(self, chat_id, text):
        """Handle service selection with better matching"""
        service = self.extract_service(text)
        
        if service:
            logger.info(f"✅ Service selected: {service} for {chat_id}")
            self.show_payment_options(chat_id, service)
        else:
            response = """
❓ I didn't catch that service. Please choose from:

💇 *Hair:* Haircut, Trim, Color
💅 *Nails:* Manicure, Pedicure  
✨ *Beauty:* Facial, Makeup

What service would you like? 💅
            """
            self.telegram.send_message(chat_id, response)
    
    def show_payment_options(self, chat_id, service):
        """Show payment options with M-Pesa status"""
        try:
            # Check M-Pesa status if not recently checked
            mpesa_status = self._get_mpesa_status()
            
            payment_message = f"""
💳 *Booking: {service.title()}*

*Service:* {service.title()}
*Deposit:* KES 1 (Test)

Choose payment method:
            """
            
            # Dynamic buttons based on M-Pesa status
            buttons = []
            
            if mpesa_status == 'active':
                buttons.append([
                    {"text": "📱 M-Pesa STK Push", "callback_data": f"mpesa_stk_{service}"},
                    {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{service}"}
                ])
            else:
                buttons.append([
                    {"text": "📱 M-Pesa (Temporarily Unavailable)", "callback_data": f"mpesa_info_{service}"},
                    {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{service}"}
                ])
            
            buttons.append([
                {"text": "💵 Pay Cash at Salon", "callback_data": f"cash_{service}"},
                {"text": "❌ Cancel", "callback_data": "cancel_booking"}
            ])
            
            self.telegram.send_message_with_buttons(chat_id, payment_message, buttons)
            logger.info(f"✅ Payment options displayed for {service}")
            
        except Exception as e:
            logger.error(f"❌ Error showing payment options: {e}")
            self.telegram.send_message(chat_id, "❌ Error loading payment options. Please try /book again.")
    
    def _get_mpesa_status(self):
        """Get cached M-Pesa status to avoid frequent checks"""
        now = datetime.now()
        
        # Cache status for 5 minutes
        if (self.last_mpesa_status and self.status_check_time and 
            (now - self.status_check_time).total_seconds() < 300):
            return self.last_mpesa_status
        
        try:
            status = self.mpesa_service.get_service_status()
            self.last_mpesa_status = status['status']
            self.status_check_time = now
            return self.last_mpesa_status
        except:
            return 'unknown'
    
    def handle_regular_message(self, chat_id, text):
        """Handle regular messages with improved matching"""
        text_lower = text.lower()
        
        # Booking triggers
        if any(word in text_lower for word in ['book', 'appointment', 'miadi', 'weka', 'nikaweke', 'reserve']):
            self.start_booking_flow(chat_id)
        # Greetings
        elif any(word in text_lower for word in ['hello', 'hi', 'hey', 'niaje', 'mambo', 'sasa', 'habari']):
            self.telegram.send_message(chat_id, "👋 Hello! Ready to book an appointment? Use /book! 💅")
        # Pricing
        elif any(word in text_lower for word in ['price', 'cost', 'how much', 'bei', 'charges']):
            self.telegram.send_message(chat_id, "💰 Services start from KES 500. Use /book to book!")
        # Services
        elif any(word in text_lower for word in ['service', 'services', 'huduma', 'what do you offer']):
            self.telegram.send_message(chat_id, "💇‍♀️ We offer haircuts, manicures, facials, and more! Use /book!")
        # Location
        elif any(word in text_lower for word in ['location', 'where', 'wapi', 'address', 'place']):
            self.telegram.send_message(chat_id, "📍 We're at Tom Mboya Street, Nairobi CBD. Open Mon-Fri 8am-7pm! 🎉")
        # Help
        elif any(word in text_lower for word in ['help', 'msaada', 'assist', 'problem']):
            self.show_help(chat_id)
        else:
            self.telegram.send_message(chat_id, "😊 I can help you book appointments! Try /book or say 'I want to book a haircut'")
    
    def handle_callback(self, callback_query):
        """Handle button callbacks with improved error handling"""
        chat_id = callback_query['message']['chat']['id']
        data = callback_query['data']
        callback_query_id = callback_query['id']
        
        logger.info(f"🔘 CALLBACK: {data}")
        self.telegram.answer_callback_query(callback_query_id, "Processing...")
        
        try:
            if data.startswith('mpesa_stk_'):
                service = data.replace('mpesa_stk_', '')
                self.start_mpesa_checkout(chat_id, service)
            elif data.startswith('mpesa_manual_'):
                service = data.replace('mpesa_manual_', '')
                self.show_manual_mpesa(chat_id, service)
            elif data.startswith('mpesa_info_'):
                service = data.replace('mpesa_info_', '')
                self.show_mpesa_info(chat_id, service)
            elif data.startswith('cash_'):
                service = data.replace('cash_', '')
                self.confirm_cash_payment(chat_id, service)
            elif data == 'cancel_booking':
                self.telegram.send_message(chat_id, "❌ Booking cancelled. Let me know if you change your mind! 😊")
                self.user_states.pop(chat_id, None)
            else:
                self.telegram.send_message(chat_id, "❌ Unknown action. Please try again.")
                
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            self.telegram.send_message(chat_id, "❌ Error processing your request. Please try again.")
    
    def start_mpesa_checkout(self, chat_id, service):
        """Start M-Pesa STK Push checkout"""
        try:
            message = f"""
📱 *M-Pesa Payment for {service.title()}*

Please reply with your *M-Pesa registered phone number*:

💰 *Amount:* KES 1 (Test)
💅 *Service:* {service.title()}

📞 *Format:* 07XXXXXXXX or 2547XXXXXXXX

I'll send a payment request to your phone! 📲
            """
            
            self.telegram.send_message(chat_id, message)
            self.user_states[chat_id] = {
                'state': 'awaiting_phone', 
                'service': service,
                'payment_method': 'mpesa_stk'
            }
            logger.info(f"✅ M-Pesa checkout started for {service}")
            
        except Exception as e:
            logger.error(f"❌ Error starting M-Pesa checkout: {e}")
            self.telegram.send_message(chat_id, "❌ Error starting payment. Please try again.")
    
    def show_mpesa_info(self, chat_id, service):
        """Show M-Pesa status information"""
        status = self._get_mpesa_status()
        
        if status != 'active':
            response = f"""
⚠️ *M-Pesa Service Notice*

M-Pesa STK Push is temporarily unavailable.

🔧 *Current Status:* {status.upper()}
💡 *You can still:*
• Use *Manual M-Pesa* option
• Pay with *Cash at Salon*
• Try again in a few minutes

We're working to restore service quickly! ⚡
            """
            self.telegram.send_message(chat_id, response)
    
    def handle_phone_input(self, chat_id, text):
        """Handle phone number input with enhanced M-Pesa handling"""
        user_state = self.user_states.get(chat_id, {})
        service = user_state.get('service', 'haircut')
        
        logger.info(f"📱 Processing M-Pesa for {service}: {text}")
        
        if self.validate_phone(text):
            # Show processing message
            processing_msg = self.telegram.send_message(chat_id, "🔄 Processing payment request...")
            
            # Use the simplified payment method
            result = self.mpesa_service.initiate_payment(
                phone_number=text,
                amount=1,
                service_name=service
            )
            
            if result['success']:
                response = f"""
✅ *Payment Request Sent!* 📱

📞 *Phone:* {text}
💰 *Amount:* KES 1
💅 *Service:* {service.title()}

📲 *Check your phone!* You should receive an M-Pesa prompt.

*Your booking is confirmed!* 🎉

{result.get('customer_message', 'Please check your phone for the M-Pesa prompt')}
                """
            else:
                error = result.get('error', 'Unknown error occurred')
                
                # Enhanced error messages
                if any(word in error.lower() for word in ['timeout', 'not responding', 'unavailable']):
                    error_section = """
⏳ *Service Temporarily Unavailable*

M-Pesa servers are not responding right now.

🔧 *Please try:*
• Wait 2-3 minutes and try again
• Use the *Manual M-Pesa* option
• Or pay with *Cash at Salon*
                    """
                elif any(word in error.lower() for word in ['connection', 'network', 'internet']):
                    error_section = """
🌐 *Network Issue*

Cannot connect to payment services.

🔧 *Please check:*
• Your internet connection
• Try using mobile data
• Contact your network provider
                    """
                elif 'invalid' in error.lower():
                    error_section = f"""
❌ *Invalid Phone Number*

Please check your phone number format.

📞 *Correct formats:*
• 07XXXXXXXX
• 2547XXXXXXXX

*You entered:* {text}
                    """
                else:
                    error_section = f"""
❌ *Payment Failed*

*Error:* {error}

🔧 *Troubleshooting:*
• Ensure phone is M-Pesa registered
• Check your M-Pesa balance
• Try manual M-Pesa option
                    """
                
                response = f"""
❌ *Payment Request Failed*

{error_section}

Your booking is *PENDING* payment confirmation.
                """
            
            self.telegram.send_message(chat_id, response)
            self.user_states.pop(chat_id, None)
        else:
            self.telegram.send_message(chat_id, "❌ Invalid phone number. Please use format: *07XXXXXXXX* or *2547XXXXXXXX*")
    
    def show_manual_mpesa(self, chat_id, service):
        """Show manual M-Pesa instructions"""
        try:
            instructions = f"""
📋 *Manual M-Pesa Payment*

*Service:* {service.title()}
*Amount:* KES 1

1. Go to *Lipa na M-Pesa*
2. Select *Pay Bill*
3. Business No: *{settings.MPESA_SHORTCODE}*
4. Account No: *FRANK{service.upper().replace(' ', '')}*
5. Amount: *1*

6. Enter your M-Pesa PIN
7. Send screenshot of confirmation

📍 *Frank Beauty Spot*
Tom Mboya Street, Nairobi CBD

*Once payment is confirmed, your booking will be secured!* 🎉
            """
            
            self.telegram.send_message(chat_id, instructions)
            logger.info(f"📋 Manual M-Pesa shown for {service}")
            
        except Exception as e:
            logger.error(f"❌ Error showing manual instructions: {e}")
            self.telegram.send_message(chat_id, "Error loading instructions. Please try /book again.")
    
    def confirm_cash_payment(self, chat_id, service):
        """Confirm cash payment with enhanced details"""
        confirmation = f"""
💵 *Booking Confirmed!* 🎉

*Service:* {service.title()}
*Deposit:* KES 500 (pay at salon)

📍 *Frank Beauty Spot*
Tom Mboya Street, Nairobi CBD

🕒 *Hours:*
Mon-Fri: 8:00 AM - 7:00 PM
Saturday: 9:00 AM - 6:00 PM
Sunday: Closed

📞 *Contact:* 07XXXXXXXX

We look forward to seeing you! 😊

*Your appointment is confirmed!* ✅
        """
        
        self.telegram.send_message(chat_id, confirmation)
        logger.info(f"💵 Cash payment confirmed for {service}")
        self.user_states.pop(chat_id, None)
    
    def show_services(self, chat_id):
        """Show available services"""
        response = """
💇‍♀️ *Our Services & Prices*

*Hair Services:*
• Haircut & Styling - KES 500-1,500
• Hair Coloring - KES 1,500-4,000
• Hair Treatment - KES 800-2,000

*Nail Services:*
• Manicure - KES 600-1,200
• Pedicure - KES 800-1,500

*Skin Care:*
• Facial Treatments - KES 1,200-2,500
• Makeup Services - KES 1,000-3,000

💡 *KES 500 deposit required to secure booking!*

Use /book to make an appointment! 😊
        """
        self.telegram.send_message(chat_id, response)
    
    def show_prices(self, chat_id):
        """Show price list"""
        response = """
💰 *Price List*

*Hair Services:*
• Haircut: KES 500-1,500
• Hair Color: KES 1,500-4,000
• Treatment: KES 800-2,000

*Nail Services:*
• Manicure: KES 600-1,200
• Pedicure: KES 800-1,500

*Skin Care:*
• Facial: KES 1,200-2,500
• Makeup: KES 1,000-3,000

💡 *Deposit:* KES 500 secures your booking!

Use /book to get started! 💅
        """
        self.telegram.send_message(chat_id, response)
    
    def check_mpesa_status(self, chat_id):
        """Check M-Pesa service status with detailed info"""
        try:
            status = self.mpesa_service.get_service_status()
            
            if status['status'] == 'active':
                response = f"""
✅ *Payment Service Status*

*Status:* ACTIVE 🟢
*Environment:* {status['environment']}
*Message:* {status['message']}

M-Pesa payments are ready to use! 🎉
                """
            else:
                response = f"""
⚠️ *Payment Service Status*

*Status:* {status['status'].upper()} 🔴
*Environment:* {status['environment']}
*Message:* {status['message']}

🔧 *Available Options:*
• Manual M-Pesa payments
• Cash payments at salon
• Try STK Push in a few minutes
                """
            self.telegram.send_message(chat_id, response)
        except Exception as e:
            self.telegram.send_message(chat_id, f"❌ Error checking payment status: {e}")
    
    def extract_service(self, text):
        """Extract service from text with improved matching"""
        text_lower = text.lower()
        
        service_map = {
            'haircut': ['haircut', 'cut', 'trim', 'nywele', 'kata', 'style'],
            'manicure': ['manicure', 'nails', 'kucha', 'fingernails'],
            'pedicure': ['pedicure', 'feet', 'miguu', 'toenails'],
            'facial': ['facial', 'face', 'uso', 'skin', 'cleaning'],
            'makeup': ['makeup', 'beat', 'make up', 'war paint'],
            'hair color': ['color', 'colour', 'dye', 'rangi', 'highlight']
        }
        
        for service, keywords in service_map.items():
            if any(word in text_lower for word in keywords):
                return service
        return None
    
    def validate_phone(self, phone):
        """Validate phone number"""
        cleaned = ''.join(filter(str.isdigit, phone))
        return (cleaned.startswith('07') and len(cleaned) == 10) or (cleaned.startswith('2547') and len(cleaned) == 12)

def run_working_booking_bot():
    """Main bot runner with Railway optimization"""
    # Get token from environment (Railway) or use default
    token = os.environ.get('TELEGRAM_TOKEN', '7582887183:AAGi83W0Kuf5VnxiqhgTwo_yUiXpNtbVzTs')
    
    # Detect environment
    environment = "RAILWAY" if 'RAILWAY' in os.environ else "LOCAL"
    
    print(f"🤖 **SALON BOOKING BOT - {environment}**")
    print("🎯 **RAILWAY OPTIMIZED VERSION**")
    print("💳 **ENHANCED MPESA HANDLING**")
    print("=" * 60)
    
    # Initialize services
    client = NetworkResilientTelegramClient(token)
    mpesa_service = MpesaService()
    
    # Test connections
    print("🔌 Testing services...")
    
    if not client.test_connection():
        print("❌ Cannot connect to Telegram. Check token and internet.")
        return
    
    # Check M-Pesa status
    mpesa_status = mpesa_service.get_service_status()
    print(f"🔑 M-Pesa Status: {mpesa_status['status'].upper()}")
    print(f"🔑 Environment: {mpesa_status['environment']}")
    print(f"🔑 Message: {mpesa_status['message']}")
    print("=" * 60)
    
    # Initialize bot
    bot = WorkingBookingBot(client)
    
    print("🔄 Starting booking bot...")
    print("💬 **QUICK START:** Send /start to your bot")
    print("📱 **TEST FLOW:** /book → 'haircut' → M-Pesa → Phone")
    print("=" * 60)
    
    # Main loop with enhanced error handling
    offset = None
    error_count = 0
    max_errors = 10
    
    while error_count < max_errors:
        try:
            updates = client.get_updates(offset=offset, timeout=10)
            
            if updates and updates.get('ok'):
                if updates.get('result'):
                    for update in updates['result']:
                        bot.handle_update(update)
                        offset = update['update_id'] + 1
                        print(f"✅ Processed update {update['update_id']}")
                    
                    print(f"📦 Processed {len(updates['result'])} updates at {datetime.now().strftime('%H:%M:%S')}")
                    error_count = 0  # Reset error count on success
                else:
                    print(f"⏳ No messages at {datetime.now().strftime('%H:%M:%S')}")
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            error_count += 1
            print(f"❌ Error #{error_count}: {e}")
            if error_count >= max_errors:
                print("🔴 Too many errors, stopping bot...")
                break
            time.sleep(5)  # Longer delay between errors

def railway_main():
    """Railway-specific entry point"""
    print("🚀 Railway Deployment Detected")
    print("🔧 Starting with Railway configuration...")
    run_working_booking_bot()

if __name__ == '__main__':
    # Detect environment and run appropriately
    if 'RAILWAY' in os.environ:
        railway_main()
    else:
        run_working_booking_bot()