# bot/handlers/command_handler.py
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self):
        self.telegram_service = None
        self.whatsapp_service = None
        self.message_handler = None
        logger.info("✅ CommandHandler initialized with multi-platform support")
    
    def _get_telegram_service(self):
        if self.telegram_service is None:
            from bot.services.telegram_service import TelegramService
            self.telegram_service = TelegramService()
        return self.telegram_service
    
    def _get_whatsapp_service(self):
        if self.whatsapp_service is None:
            from bot.services.whatsapp_service import WhatsAppService
            self.whatsapp_service = WhatsAppService()
        return self.whatsapp_service
    
    def _get_message_handler(self):
        if self.message_handler is None:
            from bot.handlers.message_handler import MessageHandler
            self.message_handler = MessageHandler()
        return self.message_handler

    def handle_command(self, chat_id, text):
        """Handle commands from Telegram"""
        try:
            parts = text.split(' ', 1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ''
            
            logger.info(f"🎯 Handling command: {command} from {chat_id}")
            
            if command == '/start':
                self.handle_start(chat_id, args, platform='telegram')
            elif command == '/book':
                self.handle_book(chat_id, args, platform='telegram')
            elif command == '/services':
                self.handle_services(chat_id, platform='telegram')
            elif command == '/prices':
                self.handle_prices(chat_id, platform='telegram')
            elif command == '/location':
                self.handle_location(chat_id, platform='telegram')
            elif command == '/help':
                self.handle_help(chat_id, platform='telegram')
            elif command == '/language':
                self.handle_language(chat_id, args, platform='telegram')
            else:
                self.handle_unknown(chat_id, command, platform='telegram')
                
        except Exception as e:
            logger.error(f"❌ Command handling error: {e}")
            self._send_response('telegram', chat_id, "❌ Sorry, there was an error processing your command.")

    async def handle_platform_command(self, user_data, command, args):
        """Handle commands from any platform"""
        try:
            platform = user_data.get('platform', 'telegram')
            user_id = user_data['user_id']
            
            logger.info(f"🎯 Handling {platform} command: {command} from {user_id}")
            
            if command == 'start':
                await self.handle_start(user_id, args, platform)
            elif command == 'book':
                await self.handle_book(user_id, args, platform)
            elif command == 'services':
                await self.handle_services(user_id, platform)
            elif command == 'prices':
                await self.handle_prices(user_id, platform)
            elif command == 'location':
                await self.handle_location(user_id, platform)
            elif command == 'help':
                await self.handle_help(user_id, platform)
            elif command == 'language':
                await self.handle_language(user_id, args, platform)
            else:
                await self.handle_unknown(user_id, command, platform)
                
        except Exception as e:
            logger.error(f"❌ Platform command handling error: {e}")
            await self._send_response_async(platform, user_id, "❌ Sorry, there was an error processing your command.")

    async def handle_start(self, user_id, args, platform='telegram'):
        """Handle /start command"""
        welcome_messages = {
            'sheng': [
                "🎉 *Mambo vipi!* Karibu Frank Beauty Spot! 😎\n\n"
                "Niko hapa kukusaidia kuweka appointments, kucheck bei, na kukupa all the deets about our services. "
                "Sema tu unataka nini, niko hapa for you! 💅✨",
                
                "🔥 *Sasa msee!* Welcome to Frank Beauty Spot!\n\n"
                "Tuko hapa kukufanyia magic - from fresh cuts to glam makeup. "
                "Just hit me with what you need, and we'll sort you out! 😊",
                
                "🌟 *Niaje fam!* Karibu kwa Frank's!\n\n"
                "I'm your beauty assistant. Naeza kukusaidia kuweka miadi, kuuliza bei, "
                "au kukupa directions. Unataka kuanza wapi? 💇‍♀️"
            ],
            'swenglish': [
                "🎉 *Habari yako!* Karibu sana kwa Frank Beauty Salon! 💅\n\n"
                "Niko hapa kukusaidia kuweka appointments, kucheck prices, na kukupa information about our services. "
                "Tafadhali niambie, how can I help you today? 😊",
                
                "✨ *Karibu!* Welcome to Frank Beauty Spot!\n\n"
                "We're excited to serve you. Ninaweza kukusaidia kuweka appointment, "
                "kuuliza bei, au kukupa directions. Ungependa nini? 💇‍♀️",
                
                "🌟 *Jambo!* Karibu kwa Frank Beauty Salon!\n\n"
                "I'm here to help you book appointments, check prices, and answer any questions. "
                "What would you like to do today? 😊"
            ],
            'english': [
                "🎉 *Hello!* Welcome to Frank Beauty Salon! 💅\n\n"
                "I'm here to help you book appointments, check prices, and provide information about our services. "
                "How may I assist you today? 😊",
                
                "✨ *Welcome!* We're delighted to have you at Frank Beauty Spot!\n\n"
                "I can help you schedule appointments, check service prices, or provide location details. "
                "What would you like to do? 💇‍♀️",
                
                "🌟 *Greetings!* Welcome to Frank Beauty Salon!\n\n"
                "As your beauty assistant, I'm here to help with bookings, pricing information, "
                "and any questions you may have. How can I help you today? 😊"
            ]
        }
        
        # Get user's language preference
        language = await self._get_user_language(platform, user_id)
        message = random.choice(welcome_messages.get(language, welcome_messages['swenglish']))
        
        # Add quick actions based on platform
        if platform == 'telegram':
            message += "\n\n*Quick actions:* /book • /services • /prices • /location"
        elif platform == 'whatsapp':
            message += "\n\n*Quick actions:* Type 'book', 'services', 'prices', or 'location'"
        
        await self._send_response_async(platform, user_id, message)

    async def handle_book(self, user_id, args, platform='telegram'):
        """Handle booking command"""
        message_handler = self._get_message_handler()
        
        if args:
            # If service is provided in command, start booking with that service
            user_data = {'platform': platform, 'user_id': user_id}
            await message_handler.start_natural_appointment(user_id, args)
        else:
            # Start general booking flow
            response = await self._get_platform_response(platform, user_id, 'booking_prompt')
            await self._send_response_async(platform, user_id, response)
            
            # Set appropriate state
            if platform == 'telegram':
                from bot.handlers.conversation_states import set_user_state, ConversationState
                set_user_state(user_id, ConversationState.APPOINTMENT_IN_PROGRESS)

    async def handle_services(self, user_id, platform='telegram'):
        """Handle services command"""
        services_info = """
💇‍♀️ *Our Beauty Services:*

✨ *Hair Services:*
• Haircut & Styling
• Hair Coloring & Treatment
• Braiding & Weaving
• Blowouts & Straightening

💅 *Nail Services:*
• Manicure (Basic, Gel, Acrylic)
• Pedicure (Basic, Spa)
• Nail Art & Design
• Nail Treatments

🌸 *Skin & Face:*
• Facial Treatments
• Skin Cleansing
• Acne Treatment
• Brightening Facials

💄 *Makeup Services:*
• Everyday Makeup
• Bridal Makeup
• Party Glam
• Photo Shoot Makeup

💆‍♀️ *Spa Services:*
• Full Body Massage
• Aromatherapy
• Hot Stone Therapy
• Relaxation Massage

*Ready to book?* Just let me know what you're interested in! 😊
        """
        await self._send_response_async(platform, user_id, services_info)

    async def handle_prices(self, user_id, platform='telegram'):
        """Handle prices command"""
        pricing_info = """
💰 *Service Prices:*

💇‍♀️ *Hair Services:*
• Haircut: KES 500 - 1,500
• Hair Color: KES 1,500 - 4,000
• Treatment: KES 800 - 2,000
• Braiding: KES 1,000 - 5,000

💅 *Nail Services:*
• Basic Manicure: KES 600
• Gel Manicure: KES 1,200
• Basic Pedicure: KES 800
• Spa Pedicure: KES 1,500

🌸 *Facial Services:*
• Basic Facial: KES 1,200
• Acne Treatment: KES 2,000
• Brightening Facial: KES 2,500

💄 *Makeup Services:*
• Everyday: KES 1,000
• Bridal: KES 3,000 - 5,000
• Party: KES 1,500 - 2,500

💆‍♀️ *Massage:*
• 30 mins: KES 1,200
• 60 mins: KES 2,000
• 90 mins: KES 2,800

*Note:* Prices may vary based on specific requirements and products used.
        """
        await self._send_response_async(platform, user_id, pricing_info)

    async def handle_location(self, user_id, platform='telegram'):
        """Handle location command"""
        location_info = """
📍 *Frank Beauty Spot*
Moi Avenue Veteran House, Room 401
Nairobi CBD, Kenya

🕒 *Operating Hours:*
Monday - Friday: 8:00 AM - 7:00 PM
Saturday: 9:00 AM - 6:00 PM
Sunday: 10:00 AM - 4:00 PM

📞 *Contact:*
Phone: +254 7XX XXX XXX
Email: info@frankbeauty.co.ke

🚗 *Getting Here:*
We're located in the city center, easily accessible by public transport.
Near Kenya National Archives building.

*We look forward to welcoming you!* 🎉
        """
        await self._send_response_async(platform, user_id, location_info)

    async def handle_help(self, user_id, platform='telegram'):
        """Handle help command"""
        help_info = """
🆘 *How I Can Help You:*

📅 *Book Appointments:*
• Use /book or say "I want to book"
• Tell me what service you need
• Choose your preferred time

💵 *Check Prices:*
• Use /prices for full price list
• Ask about specific services
• Get customized quotes

💅 *Services Info:*
• Use /services to see all services
• Get detailed service descriptions
• Ask about specific treatments

📍 *Location & Hours:*
• Use /location for address & directions
• Check operating hours
• Get contact information

🔄 *Other Features:*
• M-Pesa payment integration
• Appointment reminders
• Service recommendations

🗣️ *Language Options:*
• Use /language to switch between:
  - Sheng (informal)
  - Swenglish (mixed)
  - English (formal)

*Just talk to me naturally - I understand!* 😊
        """
        await self._send_response_async(platform, user_id, help_info)

    async def handle_language(self, user_id, args, platform='telegram'):
        """Handle language selection command"""
        if not args:
            language_options = """
🗣️ *Choose Your Language Style:*

• *Sheng* - Cool, informal, street-smart 😎
  `/language sheng`

• *Swenglish* - Mix of Swahili & English 🇰🇪
  `/language swenglish`

• *English* - Formal & professional 💼
  `/language english`

*Which style do you prefer?*
            """
            await self._send_response_async(platform, user_id, language_options)
            return
        
        language = args.lower().strip()
        valid_languages = ['sheng', 'swenglish', 'english']
        
        if language in valid_languages:
            # Update user language preference
            await self._set_user_language(platform, user_id, language)
            
            confirmation_messages = {
                'sheng': "Poa msee! 😎 Sasa tutazungumza Sheng. Unataka nini?",
                'swenglish': "Sawa! 😊 Tutazungumza Swenglish. Ungependa nini?",
                'english': "Perfect! ✅ I'll use English. How may I assist you?"
            }
            
            await self._send_response_async(platform, user_id, confirmation_messages[language])
        else:
            await self._send_response_async(platform, user_id, 
                "❌ Please choose: sheng, swenglish, or english")

    async def handle_unknown(self, user_id, command, platform='telegram'):
        """Handle unknown commands"""
        unknown_responses = {
            'sheng': [
                "Mambo? 😅 Sijaskia command hiyo. Try /book, /services, /prices, or just sema unataka nini!",
                "Sasa msee, hiyo command siko nayo. 😅 Ungependa kuweka appointment? Sema /book",
                "Niaje? Hiyo si command yangu. 😊 Try /help kujua nini naeza fanya!"
            ],
            'swenglish': [
                "Pole, sijaelewa command hiyo. 😅 Try /book, /services, /prices, or just tell me what you need!",
                "Sorry, huu command sio sahihi. 😊 Ungependa kuweka appointment? Andika /book",
                "Sielewi command hiyo. 😅 Andika /help kujua commands zote ninazozifahamu!"
            ],
            'english': [
                "Sorry, I didn't recognize that command. 😅 Try /book, /services, /prices, or just tell me what you need!",
                "I'm not familiar with that command. 😊 Would you like to book an appointment? Use /book",
                "Command not recognized. 😅 Use /help to see all available commands!"
            ]
        }
        
        language = await self._get_user_language(platform, user_id)
        response = random.choice(unknown_responses.get(language, unknown_responses['swenglish']))
        await self._send_response_async(platform, user_id, response)

    async def _get_user_language(self, platform, user_id):
        """Get user's language preference"""
        try:
            # Try to get from conversation states
            from bot.handlers.conversation_states import get_user_language
            return get_user_language(user_id)
        except:
            return 'swenglish'  # Default

    async def _set_user_language(self, platform, user_id, language):
        """Set user's language preference"""
        try:
            from bot.handlers.conversation_states import set_user_language
            set_user_language(user_id, language)
        except:
            # Fallback if conversation states not available
            pass

    async def _get_platform_response(self, platform, user_id, response_type):
        """Get platform-specific response"""
        message_handler = self._get_message_handler()
        user_data = {'platform': platform, 'user_id': user_id}
        
        # This will use the message handler's language system
        return message_handler.get_response(user_id, response_type)

    def _send_response(self, platform, user_id, message):
        """Sync response sending"""
        if platform == 'telegram':
            telegram = self._get_telegram_service()
            telegram.send_message(user_id, message)
        elif platform == 'whatsapp':
            # WhatsApp would be async, but this is sync context
            logger.info(f"📤 Would send WhatsApp message to {user_id}: {message}")

    async def _send_response_async(self, platform, user_id, message, quick_replies=None):
        """Async response sending"""
        try:
            if platform == 'telegram':
                telegram = self._get_telegram_service()
                # For async context, we'll use the existing sync method
                # In a real implementation, you might want async Telegram methods
                telegram.send_message(user_id, message)
            elif platform == 'whatsapp':
                whatsapp = self._get_whatsapp_service()
                if quick_replies:
                    await whatsapp.send_quick_reply(user_id, message, quick_replies)
                else:
                    await whatsapp.send_message(user_id, message)
        except Exception as e:
            logger.error(f"❌ Error sending {platform} response: {e}")