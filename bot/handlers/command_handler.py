# bot/handlers/command_handler.py
import logging
from bot.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self):
        self.telegram = TelegramService()
    
    def handle_command(self, chat_id, command):
        """Handle different bot commands"""
        logger.info(f"Handling command: {command} for chat: {chat_id}")
        
        if command == '/start':
            self.handle_start(chat_id)
        elif command == '/help':
            self.handle_help(chat_id)
        elif command == '/services':
            self.handle_services(chat_id)
        elif command == '/prices':
            self.handle_prices(chat_id)
        elif command == '/book':
            self.handle_book(chat_id)
        elif command == '/payment':
            self.handle_payment(chat_id)
        else:
            self.handle_unknown(chat_id)
    
    def handle_start(self, chat_id):
        welcome_text = """
👋 *Hey! Niaje?* 😊

I'm Frank from *Frank Beauty Spot*! 

Niko hapa kukusaidia:
• Weka appointment 📅 
• Angalia services zetu 💅
• Pata affordable prices 💰
• Lipa kwa M-Pesa 📱

*Sema tu unataka nini!* 💬
        """
        
        buttons = [
            [{"text": "📅 Weka Appointment", "callback_data": "book_appointment"}],
            [{"text": "💅 Angalia Services", "callback_data": "services"}],
            [{"text": "💰 Pata Prices", "callback_data": "prices"}],
            [{"text": "📱 Lipa Now", "callback_data": "payment"}],
            [{"text": "📍 Tuko Wapi?", "callback_data": "location"}]
        ]
        
        self.telegram.send_message_with_buttons(chat_id, welcome_text, buttons)
    
    def handle_help(self, chat_id):
        help_text = """
🤖 *Available Commands:*
/start - Start the bot
/help - Show this help message  
/services - View our services
/prices - Check our prices
/book - Book an appointment
/payment - Make a payment

You can also just chat with me naturally! 😊
        """
        self.telegram.send_message(chat_id, help_text, parse_mode='Markdown')
    
    def handle_services(self, chat_id):
        services_text = """
💅 *Services Tunatoa:*

*Hair Section:*
• Haircut & Styling 💇‍♀️
• Hair Color & Highlights 🎨
• Treatment & Deep Conditioning ✨
• Braids & Weaves 👑
• Dreadlocks Maintenance 🔥

*Nails & Stuff:*
• Manicure 💅
• Pedicure 👣
• Nail Art 🎨

*Face & Beauty:*
• Facials ✨
• Makeup 💄
• Eyebrows & Lashes 👁️

*Extra Vibes:*
• Waxing 🧴
• Massage 💆‍♀️

*Sema tu unataka nini, tutafute slot!* 😉
        """
        
        buttons = [
            [{"text": "💰 Price List", "callback_data": "prices"}],
            [{"text": "📅 Book Hapa", "callback_data": "book_appointment"}]
        ]
        
        self.telegram.send_message_with_buttons(chat_id, services_text, buttons)
    
    def handle_prices(self, chat_id):
        prices_text = """
💰 *Bei Zetu - Affordable Poa!*

*Hair Services:*
• Haircut - KES 500-1,500 (Simple to fancy)
• Hair Color - KES 1,500-4,000 (Depends on style)
• Treatment - KES 1,000-2,500 (Your hair will thank you)
• Braids - KES 800-3,000 (All types)
• Dreads Maintenance - KES 700-2,000

*Nails & Beauty:*
• Manicure - KES 600-1,200 (Fresh hands guaranteed)
• Pedicure - KES 800-1,500 (Feet will be happy)
• Nail Fix - KES 200-500 (Quick repair)

*Face & Makeup:*
• Facial - KES 1,200-2,500 (Glow up!)
• Makeup - KES 1,000-3,500 (From natural to glam)

*Other Goodies:*
• Waxing - KES 800-1,500
• Massage - KES 1,500-3,000 (Relax mode on)

💳 *Tukop M-Pesa? Yes! We accept Lipa Na M-Pesa*
        """
        
        buttons = [
            [{"text": "💅 Book Service", "callback_data": "book_appointment"}],
            [{"text": "📱 Lipa Now", "callback_data": "payment"}]
        ]
        
        self.telegram.send_message_with_buttons(chat_id, prices_text, buttons)
    
    def handle_book(self, chat_id):
        booking_text = """
📅 *Weka Appointment Yako!*

Sema tu the date and time ungependa kuja...
*Examples:*
• Tomorrow 2pm
• Friday morning  
• Next week Monday afternoon
• ASAP (nikupigie!)

*Au* simply tell me:
• Your preferred date
• Morning or afternoon
• "As soon as possible"
        """
        self.telegram.send_message(chat_id, booking_text)
    
    def handle_payment(self, chat_id):
        buttons = [
            [{"text": "💇 Lipa Hair Service", "callback_data": "pay_hair"}],
            [{"text": "💅 Lipa Nails", "callback_data": "pay_nails"}],
            [{"text": "✨ Lipa Facial/Makeup", "callback_data": "pay_face"}],
            [{"text": "💰 Lipa Deposit", "callback_data": "pay_deposit"}]
        ]
        self.telegram.send_message_with_buttons(chat_id, "💳 Chagua service unayotaka kulipia:", buttons)
    
    def handle_unknown(self, chat_id):
        self.telegram.send_message(chat_id, "Pole, sijaelewa command hiyo. Tumia /help kuona commands zote zilizopo.")