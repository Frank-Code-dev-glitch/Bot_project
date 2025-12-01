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

# Import conversation handler modules
from bot.handlers.conversation_states import (
    ConversationState, get_user_state, set_user_state,
    get_appointment_data, set_appointment_data, clear_appointment_data,
    add_to_conversation_history, update_last_activity
)
from bot.handlers.conversation_handler import ConversationHandler

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
    """Booking bot with ConversationHandler integration"""
    
    def __init__(self, telegram_client):
        self.telegram = telegram_client
        self.mpesa_service = MpesaService()
        self.user_states = {}
        self.last_mpesa_status = None
        self.status_check_time = None
        
        # Initialize ConversationHandler
        self.conversation_handler = ConversationHandler(self)
        
        logger.info("✅ WorkingBookingBot initialized with ConversationHandler")
    
    # ===== MAIN HANDLER METHODS =====
    
    def handle_update(self, update):
        """Handle all updates with ConversationHandler integration"""
        try:
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
        except Exception as e:
            logger.error(f"Error handling update: {e}")
    
    def handle_message(self, message):
        """Handle incoming messages with ConversationHandler"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        
        logger.info(f"📨 Message from {chat_id}: {text}")
        
        if text.startswith('/'):
            self.handle_command(chat_id, text)
        else:
            # Update activity timestamp
            update_last_activity(chat_id)
            
            # Add to conversation history
            add_to_conversation_history(chat_id, 'user', text)
            
            # Process through ConversationHandler
            response = self.conversation_handler.process_message(chat_id, text)
            
            if response:
                # Send the response from ConversationHandler
                self.telegram.send_message(chat_id, response)
    
    def handle_command(self, chat_id, text):
        """Handle bot commands"""
        command = text.lower().strip()
        
        if command == '/start':
            self.send_welcome_message(chat_id)
        elif command == '/book':
            self.conversation_handler.start_appointment_flow(chat_id)
        elif command == '/services':
            self.conversation_handler.bot.send_services_list(chat_id)
        elif command == '/prices':
            self.show_prices(chat_id)
        elif command == '/status':
            self.check_mpesa_status(chat_id)
        elif command == '/help':
            self.show_help(chat_id)
        elif command == '/clear':
            # Clear conversation state (for testing)
            from bot.handlers.conversation_states import clear_user_state
            clear_user_state(chat_id)
            self.telegram.send_message(chat_id, "🔄 Conversation state cleared!")
        else:
            self.telegram.send_message(chat_id, "❌ Unknown command. Try /start for available commands.")
    
    # ===== METHODS FOR CONVERSATION HANDLER =====
    
    def send_message(self, chat_id, message):
        """Send message - used by ConversationHandler"""
        return self.telegram.send_message(chat_id, message)
    
    def send_greeting(self, chat_id):
        """Send greeting - called by ConversationHandler"""
        response = """
👋 *Karibu kwa Frank Beauty Spot!* 💅

Niko hapa kukusaidia kuweka appointment!

*Unaweza:*
📅 Kuweka miadi ya huduma
💰 Kuuliza bei za services
📍 Kujua location yetu
❓ Kuuliza maswali yoyote

*Au andika tu:* "Nataka kuweka appointment ya haircut"

Tuko pamoja! 😊
        """
        return self.send_message(chat_id, response)
    
    def send_services_list(self, chat_id):
        """Send services list - called by ConversationHandler"""
        response = """
💇‍♀ *SERVICES ZETU & BEI* 💅

*Hair Services:*
• Haircut & Styling - Kuanzia KES 500
• Hair Coloring - Kuanzia KES 1,500

*Nail Services:*
• Manicure/Pedicure - Kuanzia KES 600

*Skin Care:*
• Facial Treatment - Kuanzia KES 1,200
• Makeup Services - Kuanzia KES 1,000

*Ungependa service gani?* 😊

*Au unaswali lingine?*
        """
        return self.send_message(chat_id, response)
    
    def ask_for_service(self, chat_id):
        """Ask for service - called by ConversationHandler"""
        response = """*Tuko pamoja!* 💅

Service gani ungependa kuweka appointment?
- Haircut & Styling
- Hair Coloring
- Manicure/Pedicure
- Facial Treatment
- Makeup Services

*Tafadhali niambie service unayotaka.*"""
        return self.send_message(chat_id, response)
    
    def ask_for_service_with_time(self, chat_id, time_info):
        """Ask for service when time is mentioned"""
        response = f"""*Perfect!* Unasema {time_info}. 💅

Service gani ungependa?
- Haircut & Styling
- Hair Coloring
- Manicure/Pedicure
- Facial Treatment
- Makeup Services

*Tafadhali chagua service moja.*"""
        return self.send_message(chat_id, response)
    
    def ask_for_date(self, chat_id, service):
        """Ask for date - called by ConversationHandler"""
        response = f"""*Nimepata!* {service} itakuwa poa! 📅

*Ungepanda lini?*
- Leo (today)
- Kesho (tomorrow) 
- Jumatatu (Monday)
- Ipe tarehe maalum (e.g., 15 Dec)

*Tafadhali niambie siku.*"""
        return self.send_message(chat_id, response)
    
    def ask_for_time(self, chat_id):
        """Ask for time - called by ConversationHandler"""
        response = """*Sawa!* ⏰

*Saa ngapi ungependa?*
- Asubuhi (morning) - 9 AM mpaka 12 PM
- Mchana (afternoon) - 2 PM mpaka 5 PM  
- Jioni (evening) - 6 PM mpaka 8 PM
- Ipe saa maalum (e.g., 2:30 PM)

*Tafadhali niambie saa.*"""
        return self.send_message(chat_id, response)
    
    def ask_for_name(self, chat_id, service):
        """Ask for name - called by ConversationHandler"""
        response = f"""*Karibu sana!* 👤

Ili kukusanyia appointment ya {service}, tafadhali niambie:
*Jina lako nani?*"""
        return self.send_message(chat_id, response)
    
    def ask_for_name_with_time(self, chat_id, service, time_info):
        """Ask for name when time is already specified"""
        response = f"""*Perfect!* {service} {time_info}. 👤

*Tafadhali niambie jina lako:*"""
        return self.send_message(chat_id, response)
    
    def ask_for_phone(self, chat_id):
        """Ask for phone - called by ConversationHandler"""
        response = """*Asante!* 📱

*Tafadhali nipe namba yako ya simu* (mfano: 0712345678):"""
        return self.send_message(chat_id, response)
    
    def ask_for_confirmation(self, chat_id, appointment):
        """Ask for confirmation - called by ConversationHandler"""
        summary = f"""📋 *MUHTASARI WA APPOINTMENT* ✅

*Service:* {appointment.get('service', 'Haircut & Styling')}
*Siku:* {appointment.get('date', 'Kesho')}
*Saa:* {appointment.get('time', '2:00 PM')}
*Jina:* {appointment.get('customer_name', 'Mgeni')}
*Simu:* {appointment.get('customer_phone', 'Hajapewa')}

---
*Je, taarifa hizi ziko sawa?*

*Andika 'NDIO' kuconfirm AU 'HAPANA' kubadilisha.*"""
        return self.send_message(chat_id, summary)
    
    def save_appointment(self, chat_id, appointment):
        """Save appointment to database"""
        try:
            from bot.models import Appointment
            
            # Create appointment in database
            Appointment.objects.create(
                customer_whatsapp=str(chat_id),
                service_type=appointment.get('service', 'Haircut & Styling'),
                appointment_date=appointment.get('date', datetime.now().date()),
                appointment_time=appointment.get('time', '14:00'),
                customer_name=appointment.get('customer_name', 'Customer'),
                customer_phone=appointment.get('customer_phone', ''),
                status='pending',
                created_at=datetime.now()
            )
            
            logger.info(f"✅ Appointment saved for {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving appointment: {e}")
            return False
    
    def send_payment_options(self, chat_id, appointment):
        """Send payment options - called by ConversationHandler"""
        # Get M-Pesa status
        mpesa_status = self._get_mpesa_status()
        
        # Build message based on M-Pesa status
        if mpesa_status == 'active':
            mpesa_section = """📱 *M-PESA STK PUSH*
   - Chagua option ya M-Pesa
   - Nipe namba yako ya simu
   - Utapokea prompt kwenye simu"""
        else:
            mpesa_section = """📱 *M-PESA (Manual)*
   - Lipa kwa paybill
   - Tuma confirmation"""
        
        message = f"""💰 *OPTIONS ZA KULIPIA* 💳

*Appointment:* {appointment.get('service')}
*Service:* KES {self._get_service_price(appointment.get('service'))}

{mpesa_section}

💵 *CASH ON ARRIVAL*
   - Lipia ukiwa salonini

*Tafadhali chagua njia ya malipo:*"""
        
        # Create payment buttons
        buttons = []
        if mpesa_status == 'active':
            buttons.append([
                {"text": "📱 M-Pesa STK", "callback_data": f"mpesa_stk_{appointment.get('service')}"},
                {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{appointment.get('service')}"}
            ])
        else:
            buttons.append([
                {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{appointment.get('service')}"}
            ])
        
        buttons.append([
            {"text": "💵 Cash at Salon", "callback_data": f"cash_{appointment.get('service')}"},
            {"text": "❌ Cancel", "callback_data": "cancel_booking"}
        ])
        
        # Send message with buttons
        return self.telegram.send_message_with_buttons(chat_id, message, buttons)
    
    def _get_service_price(self, service):
        """Get price for a service"""
        prices = {
            'Haircut & Styling': '500-1,500',
            'Hair Coloring': '1,500-4,000',
            'Manicure/Pedicure': '600-1,500',
            'Facial Treatment': '1,200-2,500',
            'Makeup Services': '1,000-3,000'
        }
        return prices.get(service, '500-2,000')
    
    # ===== EXISTING METHODS (preserved) =====
    
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
        self.send_message(chat_id, response)
    
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
        self.send_message(chat_id, response)
    
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
        self.send_message(chat_id, response)
    
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
            self.send_message(chat_id, response)
        except Exception as e:
            self.send_message(chat_id, f"❌ Error checking payment status: {e}")
    
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
                # Clear conversation state
                from bot.handlers.conversation_states import clear_user_state
                clear_user_state(chat_id)
                self.send_message(chat_id, "❌ Booking cancelled. Let me know if you change your mind! 😊")
            else:
                self.send_message(chat_id, "❌ Unknown action. Please try again.")
                
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            self.send_message(chat_id, "❌ Error processing your request. Please try again.")
    
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
            
            self.send_message(chat_id, message)
            self.user_states[chat_id] = {
                'state': 'awaiting_phone', 
                'service': service,
                'payment_method': 'mpesa_stk'
            }
            logger.info(f"✅ M-Pesa checkout started for {service}")
            
        except Exception as e:
            logger.error(f"❌ Error starting M-Pesa checkout: {e}")
            self.send_message(chat_id, "❌ Error starting payment. Please try again.")
    
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
            self.send_message(chat_id, response)
    
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
            
            self.send_message(chat_id, instructions)
            logger.info(f"📋 Manual M-Pesa shown for {service}")
            
        except Exception as e:
            logger.error(f"❌ Error showing manual instructions: {e}")
            self.send_message(chat_id, "Error loading instructions. Please try /book again.")
    
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
        
        self.send_message(chat_id, confirmation)
        logger.info(f"💵 Cash payment confirmed for {service}")
        # Clear conversation state after confirmation
        from bot.handlers.conversation_states import clear_user_state
        clear_user_state(chat_id)
    
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
    
    def extract_service(self, text):
        """Extract service from text with improved matching"""
        text_lower = text.lower()
        
        service_map = {
            'Haircut & Styling': ['haircut', 'cut', 'trim', 'nywele', 'kata', 'style', 'hair'],
            'Manicure/Pedicure': ['manicure', 'nails', 'kucha', 'fingernails', 'pedicure', 'feet'],
            'Facial Treatment': ['facial', 'face', 'uso', 'skin', 'cleaning', 'treatment'],
            'Makeup Services': ['makeup', 'beat', 'make up', 'war paint', 'make-up'],
            'Hair Coloring': ['color', 'colour', 'dye', 'rangi', 'highlight', 'coloring']
        }
        
        for service, keywords in service_map.items():
            if any(word in text_lower for word in keywords):
                return service
        return None

def run_working_booking_bot():
    """Main bot runner with Railway optimization"""
    # Get token from environment (Railway) or use default
    token = os.environ.get('TELEGRAM_TOKEN', '7582887183:AAGi83W0Kuf5VnxiqhgTwo_yUiXpNtbVzTs')
    
    # Detect environment
    environment = "RAILWAY" if 'RAILWAY' in os.environ else "LOCAL"
    
    print(f"🤖 **SALON BOOKING BOT - {environment}**")
    print("🎯 **CONVERSATION HANDLER INTEGRATION**")
    print("💬 **SMART CONVERSATION FLOW**")
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
    
    print("🔄 Starting bot with ConversationHandler...")
    print("💬 **NEW SMART FLOW:**")
    print("1. User: 'What services do you offer?'")
    print("2. Bot: Shows services list")
    print("3. User: 'Haircut'")
    print("4. Bot: Starts booking flow automatically")
    print("=" * 60)
    print("📱 **TEST COMMANDS:**")
    print("/start - Welcome message")
    print("/book - Start booking")
    print("/clear - Clear conversation state")
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