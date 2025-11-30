# bot/handlers/message_handler.py
import logging
import re
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Define ConversationState locally to avoid import issues
class ConversationState:
    IDLE = "idle"
    APPOINTMENT_IN_PROGRESS = "appointment_in_progress"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_PAYMENT = "awaiting_payment"
    CHOOSING_LANGUAGE = "choosing_language"

class MessageHandler:
    def __init__(self):
        # Lazy imports to avoid circular imports
        self.command_handler = None
        self.ai_service = None
        self.memory = None
        self.knowledge = None
        self.telegram = None
        self.payment_handler = None
        
        # Language and cultural responses
        self.language_styles = {
            'sheng': {
                'greeting': [
                    "Mambo vipi boss! 😎 Frank Beauty Spot iko ready kukutreat! Unapenda nini leo?",
                    "Sasa msee! 💅 Karibu Frank's, tunaeza kusettle hair yako, makeup, the works!",
                    "Niaje fam! Welcome to Frank Beauty Spot. Tuko hapa kukufanyia magic! ✨"
                ],
                'booking_prompt': "Uko ready kuweka appointment? Sema tu service unataka na tutaplan!",
                'service_question': "So msee, unataka nini exactly? Haircut, manicure, facial, makeup? Spill the tea! ☕",
                'confirmation': "Poa! Tumeconfirm appointment yako. Tutakuona kwa salon! 🔥",
                'payment': "To lock your slot, tafadhali lipa KSh {amount} through M-Pesa. Simple!",
                'thanks': "Asante mzee! Uko solid. Karibu tena anytime! 🙌"
            },
            'swenglish': {
                'greeting': [
                    "Habari yako! Welcome to Frank Beauty Salon. How can we make you beautiful today? 💅",
                    "Karibu sana! We're excited to serve you. What treatment would you like? ✨",
                    "Jambo! Welcome to Frank Beauty Spot. Tuko hapa kukupatia the best beauty experience. 😊"
                ],
                'booking_prompt': "Would you like to book an appointment? Tafadhali tell me what service unataka.",
                'service_question': "Which service ungependa? We have haircut, manicure, pedicure, facial, na makeup.",
                'confirmation': "Perfect! Tumeconfirm your appointment. Tutakuona on the scheduled date! ✅",
                'payment': "Tafadhali make payment of KSh {amount} through M-Pesa to secure your booking.",
                'thanks': "Asante sana for choosing us! We look forward to serving you. 🎉"
            },
            'english': {
                'greeting': [
                    "Hello! Welcome to Frank Beauty Salon! How may I assist you today? 💇‍♀️",
                    "Good day! Ready for your beauty transformation? What can I help you with? ✨",
                    "Welcome to Frank Beauty Spot! We're here to make you feel fabulous. 😊"
                ],
                'booking_prompt': "Would you like to schedule an appointment? Please tell me what service you're interested in.",
                'service_question': "What service would you like? We offer haircuts, manicures, facials, and makeup services.",
                'confirmation': "Excellent! Your appointment has been confirmed. We'll see you then! ✅",
                'payment': "Please complete your payment of KSh {amount} via M-Pesa to secure your appointment.",
                'thanks': "Thank you for choosing Frank Beauty Salon! We appreciate your business. 🎉"
            }
        }
        
        self.service_mapping = {
            'hair': ['hair', 'nywele', 'cut', 'trim', 'style', 'blow', 'braid'],
            'nails': ['nail', 'manicure', 'pedicure', 'kucha', 'polish'],
            'face': ['facial', 'face', 'uso', 'skin', 'cleanse'],
            'makeup': ['makeup', 'beat', 'glam', 'foundation', 'lipstick'],
            'massage': ['massage', 'massaji', 'relax', 'spa']
        }
        
        logger.info("✅ MessageHandler initialized with Kenyan language support")

    def _get_command_handler(self):
        if self.command_handler is None:
            from bot.handlers.command_handler import CommandHandler
            self.command_handler = CommandHandler()
        return self.command_handler
    
    def _get_ai_service(self):
        if self.ai_service is None:
            from bot.services.huggingface_service import HuggingFaceService
            self.ai_service = HuggingFaceService()
        return self.ai_service
    
    def _get_memory(self):
        if self.memory is None:
            from bot.services.customer_memory import CustomerMemory
            self.memory = CustomerMemory()
        return self.memory
    
    def _get_knowledge(self):
        if self.knowledge is None:
            from bot.knowledge.salon_knowledge import SalonKnowledge
            self.knowledge = SalonKnowledge()
        return self.knowledge
    
    def _get_telegram(self):
        if self.telegram is None:
            from bot.services.telegram_service import TelegramService
            self.telegram = TelegramService()
        return self.telegram
    
    def _get_payment_handler(self):
        if self.payment_handler is None:
            from bot.handlers.payment_handler import PaymentHandler
            self.payment_handler = PaymentHandler()
        return self.payment_handler
    
    def _get_conversation_states(self):
        """Get conversation state functions with fallback"""
        try:
            from bot.handlers.conversation_states import (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            )
            return (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            )
        except ImportError:
            logger.warning("Conversation states module not found, using fallback")
            return self._create_fallback_states()
    
    def _create_fallback_states(self):
        """Create fallback state management functions"""
        user_states = {}
        appointment_data = {}
        conversation_context = {}
        user_language = {}  # Track user language preference
        
        def get_user_state(chat_id):
            return user_states.get(chat_id, ConversationState.IDLE)
        
        def set_user_state(chat_id, state):
            user_states[chat_id] = state
        
        def clear_user_state(chat_id):
            user_states.pop(chat_id, None)
        
        def get_appointment_data(chat_id):
            return appointment_data.get(chat_id, {})
        
        def set_appointment_data(chat_id, data):
            appointment_data[chat_id] = data
        
        def clear_appointment_data(chat_id):
            appointment_data.pop(chat_id, None)
        
        def get_conversation_context(chat_id):
            return conversation_context.get(chat_id, {})
        
        def set_conversation_context(chat_id, context):
            conversation_context[chat_id] = context
            
        def get_user_language(chat_id):
            return user_language.get(chat_id, 'swenglish')  # Default to Swenglish
        
        def set_user_language(chat_id, language):
            user_language[chat_id] = language
            
        return (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        )

    def detect_language_preference(self, text):
        """Detect user's language preference from their message"""
        text_lower = text.lower()
        
        # Sheng indicators
        sheng_words = ['mambo', 'sasa', 'niaje', 'msee', 'boss', 'vipi', 'poa', 'sawa', 'fiti']
        if any(word in text_lower for word in sheng_words):
            return 'sheng'
        
        # Swahili indicators
        swahili_words = ['habari', 'karibu', 'asante', 'tafadhali', 'unataka', 'nini', 'huduma']
        if any(word in text_lower for word in swahili_words):
            return 'swenglish'
        
        # English indicators
        if re.search(r'\b(hello|hi|hey|book|appointment|service|price)\b', text_lower):
            return 'english'
            
        return 'swenglish'  # Default

    def get_response(self, chat_id, response_type, **kwargs):
        """Get response in user's preferred language"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        language = get_user_language(chat_id)
        responses = self.language_styles.get(language, self.language_styles['swenglish'])
        
        response = random.choice(responses[response_type]) if isinstance(responses[response_type], list) else responses[response_type]
        
        # Format with kwargs
        return response.format(**kwargs)

    def handle_update(self, update):
        """Main handler for all Telegram updates"""
        try:
            logger.info(f"Processing update: {update}")
            
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
            else:
                logger.warning(f"Unhandled update type: {update}")
        except Exception as e:
            logger.error(f"Error handling update: {e}")

    def handle_message(self, message):
        """Handle incoming messages with language detection"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        
        logger.info(f"📨 Processing message from {chat_id}: {text}")
        
        # Get services
        telegram = self._get_telegram()
        command_handler = self._get_command_handler()
        
        # Get conversation states
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        # Detect and set language preference on first message
        current_language = get_user_language(chat_id)
        if not current_language or get_user_state(chat_id) == ConversationState.IDLE:
            detected_language = self.detect_language_preference(text)
            set_user_language(chat_id, detected_language)
            logger.info(f"🗣️ Detected language preference for {chat_id}: {detected_language}")
        
        # Record customer interaction
        try:
            memory = self._get_memory()
            memory.remember_customer(chat_id)
        except Exception as e:
            logger.error(f"Error remembering customer: {e}")
        
        # Check user state first
        user_state = get_user_state(chat_id)
        
        if user_state == ConversationState.CHOOSING_LANGUAGE:
            self.handle_language_selection(chat_id, text)
        elif user_state != ConversationState.IDLE:
            self.handle_appointment_conversation(chat_id, text, user_state)
        elif text.startswith('/'):
            command_handler.handle_command(chat_id, text)
        else:
            # Check if this is payment context
            appointment_data = get_appointment_data(chat_id)
            if appointment_data and appointment_data.get('awaiting_phone'):
                self.handle_payment_message(chat_id, text)
            elif self.is_appointment_intent(text):
                self.start_natural_appointment(chat_id, text)
            elif self.is_language_switch_request(text):
                self.offer_language_options(chat_id)
            else:
                response = self.generate_cultural_response(chat_id, text)
                
                # Record the conversation
                try:
                    memory = self._get_memory()
                    memory.record_conversation(chat_id, text, response)
                except Exception as e:
                    logger.error(f"Error recording conversation: {e}")
                
                telegram.send_message(chat_id, response)

    def generate_cultural_response(self, chat_id, user_message):
        """Generate response using Kenyan cultural context"""
        message_lower = user_message.lower()
        
        # Get user's language preference
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        language = get_user_language(chat_id)
        
        # Greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'mambo', 'niaje', 'sasa', 'habari']):
            return self.get_response(chat_id, 'greeting')
        
        # Service inquiries
        elif any(word in message_lower for word in ['service', 'huduma', 'nini', 'offer', 'do']):
            return self.get_service_options(chat_id)
        
        # Price inquiries
        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'bei', 'pesa']):
            return self.get_pricing_info(chat_id)
        
        # Location inquiries
        elif any(word in message_lower for word in ['where', 'location', 'wapi', 'place', 'address']):
            return self.get_location_info(chat_id)
        
        # Booking intent
        elif self.is_appointment_intent(message_lower):
            return self.get_response(chat_id, 'booking_prompt')
        
        # Payment inquiries
        elif any(word in message_lower for word in ['pay', 'payment', 'mpesa', 'lipa', 'cash']):
            return self.get_payment_info(chat_id)
        
        # Thanks
        elif any(word in message_lower for word in ['thank', 'thanks', 'asante', 'shukran']):
            return self.get_response(chat_id, 'thanks')
        
        # Default engaging response
        else:
            return self.get_engaging_fallback(chat_id, user_message)

    def get_service_options(self, chat_id):
        """Get service options in user's preferred language"""
        language = self._get_conversation_states()[-2](chat_id)  # get_user_language
        
        if language == 'sheng':
            return """
💅 *Services Zetu:*
• *Haircut & Styling* - From KES 500
• *Manicure/Pedicure* - From KES 600  
• *Facial Treatment* - From KES 1,200
• *Makeup Services* - From KES 1,000
• *Hair Coloring* - From KES 1,500

*Unataka nini exactly?* Sema tu! 😎
            """
        elif language == 'swenglish':
            return """
💇‍♀️ *Our Services:*
• *Haircut & Styling* - From KES 500
• *Manicure/Pedicure* - From KES 600
• *Facial Treatment* - From KES 1,200  
• *Makeup Services* - From KES 1,000
• *Hair Coloring* - From KES 1,500

*Ungependa which service?* Tafadhali tell me! 😊
            """
        else:
            return """
💇‍♀️ *Our Services:*
• Haircut & Styling - From KES 500
• Manicure/Pedicure - From KES 600
• Facial Treatment - From KES 1,200
• Makeup Services - From KES 1,000
• Hair Coloring - From KES 1,500

*Which service interests you?* Let me know! 😊
            """

    def get_pricing_info(self, chat_id):
        """Get pricing information"""
        language = self._get_conversation_states()[-2](chat_id)
        
        if language == 'sheng':
            return """
💰 *Bei Zetu:*
• Haircut: KES 500-1,500
• Hair Color: KES 1,500-4,000  
• Manicure: KES 600-1,200
• Pedicure: KES 800-1,500
• Facial: KES 1,200-2,500
• Makeup: KES 1,000-3,000

*Ready kuweka appointment?* Just say *'nataka kuweka appointment'*! 🔥
            """
        else:
            return """
💰 *Our Prices:*
• Haircut: KES 500-1,500
• Hair Color: KES 1,500-4,000  
• Manicure: KES 600-1,200
• Pedicure: KES 800-1,500
• Facial: KES 1,200-2,500
• Makeup: KES 1,000-3,000

*Ready to book?* Just say *'I want to book'*! 💅
            """

    def get_location_info(self, chat_id):
        """Get location information"""
        return """
📍 *Frank Beauty Spot*
Moi Avenue veteran house room 401, Nairobi CBD

*Hours:*
Mon-Fri: 8am - 7pm
Sat: 9am - 6pm  
Sun: 10am - 4pm

*Come visit us!* 🎉
        """

    def get_payment_info(self, chat_id):
        """Get payment information"""
        language = self._get_conversation_states()[-2](chat_id)
        
        if language == 'sheng':
            return """
💳 *Malipo:*
• M-Pesa STK Push (automatic)
• Manual M-Pesa 
• Cash kwa salon

*Ready kuweka appointment?* Sema *'nataka kuweka'* na tutaanza! 💅
            """
        else:
            return """
💳 *Payment Options:*
• M-Pesa STK Push (automatic)
• Manual M-Pesa 
• Cash at salon

*Ready to book?* Say *'book appointment'* to get started! 💅
            """

    def get_engaging_fallback(self, chat_id, user_message):
        """Get engaging fallback response"""
        language = self._get_conversation_states()[-2](chat_id)
        
        if language == 'sheng':
            responses = [
                "Mambo! Niko hapa kukusaidia! 💅 Unataka kuweka appointment, kuuliza bei, au kujua services zetu?",
                "Sasa msee! Natumai uko fiti. Nisaidie kukusaidia - unapenda nini? 😎",
                "Niaje fam! Tuko hapa kukufanyia magic. Sema tu unataka nini! ✨"
            ]
        elif language == 'swenglish':
            responses = [
                "Niko hapa kukusaidia! 💅 Unataka kuweka appointment, kuuliza bei, au kujua services zetu?",
                "I'd love to help! 😊 You can ask me about prices, book an appointment, or learn about our services!",
                "Karibu! How can I assist you today? 💅 You can book appointments, check prices, or ask about services!"
            ]
        else:
            responses = [
                "I'm here to help! 💅 You can book appointments, check prices, or learn about our services!",
                "How can I assist you today? 😊 You can ask about our services, prices, or book an appointment!",
                "Welcome! I can help you book appointments, check prices, or answer any questions! 💇‍♀️"
            ]
        
        return random.choice(responses)

    def is_language_switch_request(self, text):
        """Check if user wants to switch language"""
        language_words = ['english', 'swahili', 'sheng', 'language', 'lugha', 'zungumza']
        return any(word in text.lower() for word in language_words)

    def offer_language_options(self, chat_id):
        """Offer language options to user"""
        telegram = self._get_telegram()
        
        message = """
🗣️ *Choose your preferred language:*

• *Sheng* - For the cool, informal vibe 😎
• *Swenglish* - Mix of Swahili & English 🇰🇪  
• *English* - Formal and professional 💼

*Reply with your choice!*
        """
        
        telegram.send_message(chat_id, message)
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        set_user_state(chat_id, ConversationState.CHOOSING_LANGUAGE)

    def handle_language_selection(self, chat_id, text):
        """Handle language selection"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        text_lower = text.lower()
        
        if 'sheng' in text_lower or 'informal' in text_lower:
            set_user_language(chat_id, 'sheng')
            telegram.send_message(chat_id, "Poa msee! 😎 Sasa tuko on the same page. Unataka nini?")
        elif 'english' in text_lower or 'formal' in text_lower:
            set_user_language(chat_id, 'english')
            telegram.send_message(chat_id, "Perfect! I'll use English. How may I assist you today?")
        elif 'swenglish' in text_lower or 'swahili' in text_lower:
            set_user_language(chat_id, 'swenglish')
            telegram.send_message(chat_id, "Sawa! Tutazungumza Swenglish. Unataka nini? 😊")
        else:
            telegram.send_message(chat_id, "Please choose: Sheng, Swenglish, or English")
            return
        
        set_user_state(chat_id, ConversationState.IDLE)

    def start_natural_appointment(self, chat_id, user_message):
        """Start natural appointment conversation"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            ) = self._get_conversation_states()
            
            # Extract service intent from message
            service_intent = self.extract_service_intent(user_message)
            
            set_appointment_data(chat_id, {'service_intent': service_intent})
            set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
            
            telegram = self._get_telegram()
            
            if service_intent:
                # If service is clear, ask for timing
                response = self.get_response(chat_id, 'service_question')
                telegram.send_message(chat_id, f"{response} (We got: {service_intent})")
            else:
                # Ask about service preference
                telegram.send_message(chat_id, self.get_response(chat_id, 'service_question'))
            
        except Exception as e:
            logger.error(f"Error starting natural appointment: {e}")

    def extract_service_intent(self, text):
        """Extract service intent from natural language"""
        text_lower = text.lower()
        
        for service, keywords in self.service_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                return service
        return None

    # ... (keep all your existing handle_payment_message, handle_callback, 
    # handle_appointment_conversation, continue_appointment_flow methods as they are)
    # They will automatically use the new language system through get_response()

    def is_appointment_intent(self, text):
        """Detect if user wants to book an appointment"""
        appointment_keywords = [
            'book', 'appointment', 'schedule', 'reserve', 'miadi',
            'come in', 'visit', 'see you', 'available', 'free',
            'nikaweke', 'tengeneza', 'weka', 'ingia', 'nataka', 'I want',
            'need', 'would like', 'napenda'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in appointment_keywords)

    # ... (keep all your existing platform methods from the previous version)
    async def handle_platform_message(self, user_data, message_text):
        """Handle messages from any platform"""
        try:
            platform = user_data.get('platform', 'telegram')
            user_id = user_data['user_id']
            
            logger.info(f"🔄 Handling {platform} message from {user_id}: {message_text}")
            
            # For WhatsApp, use the same natural language processing
            if platform == 'whatsapp':
                # Convert to Telegram-like format for existing handlers
                update = {
                    'message': {
                        'chat': {'id': user_id},
                        'text': message_text,
                        'from': {'id': user_id}
                    }
                }
                self.handle_update(update)
            else:
                # Existing Telegram handling
                self.handle_update({
                    'message': {
                        'chat': {'id': user_id},
                        'text': message_text,
                        'from': {'id': user_id}
                    }
                })
                    
        except Exception as e:
            logger.error(f"❌ Error handling platform message: {e}")

    async def send_platform_response(self, user_data, response_text, quick_replies=None):
        """Send response through appropriate platform"""
        try:
            platform = user_data['platform']
            user_id = user_data['user_id']
            
            if platform == 'whatsapp':
                from ..services.whatsapp_service import WhatsAppService
                service = WhatsAppService()
            else:
                from ..services.telegram_service import TelegramService
                service = TelegramService()
            
            if quick_replies:
                await service.send_quick_reply(user_id, response_text, quick_replies)
            else:
                await service.send_message(user_id, response_text)
                
        except Exception as e:
            logger.error(f"❌ Error sending platform response: {e}")