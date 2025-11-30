# bot/handlers/message_handler.py
import logging
import re
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class ConversationState:
    """Conversation states for the bot"""
    IDLE = "idle"
    APPOINTMENT_IN_PROGRESS = "appointment_in_progress"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_PAYMENT = "awaiting_payment"
    CHOOSING_LANGUAGE = "choosing_language"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_SERVICE = "awaiting_service"
    AWAITING_TIME = "awaiting_time"

class MessageHandler:
    """
    Main message handler for Frank Beauty Spot bot
    Supports multiple platforms (Telegram, WhatsApp) with Kenyan cultural adaptation
    """
    
    def __init__(self):
        # Lazy imports to avoid circular imports
        self.command_handler = None
        self.ai_service = None
        self.memory = None
        self.knowledge = None
        self.telegram = None
        self.payment_handler = None
        self.whatsapp_service = None
        
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
                'thanks': "Asante mzee! Uko solid. Karibu tena anytime! 🙌",
                'payment_prompt': "Tafadhali tuma namba yako ya simu kwa M-Pesa payment...",
                'time_question': "Sawa! {service} it is! 💅\n\nWhen unataka kuingia? (e.g., 'kesho 2pm', 'Friday morning')"
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
                'thanks': "Asante sana for choosing us! We look forward to serving you. 🎉",
                'payment_prompt': "Tafadhali provide your phone number for M-Pesa payment...",
                'time_question': "Nice! {service} it is! 💅\n\nWhen would you like to come? (e.g., 'tomorrow 2pm', 'Friday morning')"
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
                'thanks': "Thank you for choosing Frank Beauty Salon! We appreciate your business. 🎉",
                'payment_prompt': "Please provide your phone number for M-Pesa payment...",
                'time_question': "Great choice! {service} it is! 💅\n\nWhen would you like to come? (e.g., 'tomorrow 2pm', 'Friday morning')"
            }
        }
        
        self.service_mapping = {
            'hair': ['hair', 'nywele', 'cut', 'trim', 'style', 'blow', 'braid', 'weave', 'haircut', 'styling', 'blowout'],
            'nails': ['nail', 'manicure', 'pedicure', 'kucha', 'polish', 'gel', 'nails', 'manicure', 'pedicure'],
            'face': ['facial', 'face', 'uso', 'skin', 'cleanse', 'treatment', 'facial', 'skincare'],
            'makeup': ['makeup', 'beat', 'glam', 'foundation', 'lipstick', 'eye', 'make up', 'make-up', 'bridal'],
            'massage': ['massage', 'massaji', 'relax', 'spa', 'therapy', 'body massage']
        }
        
        self.service_prices = {
            'hair': {'min': 500, 'max': 4000, 'default': 800},
            'nails': {'min': 600, 'max': 2500, 'default': 800},
            'face': {'min': 1200, 'max': 3500, 'default': 1500},
            'makeup': {'min': 1000, 'max': 5000, 'default': 2000},
            'massage': {'min': 1500, 'max': 4000, 'default': 2000}
        }
        
        logger.info("✅ MessageHandler initialized with Kenyan language support")

    # === Service Getters (Lazy Loading) ===
    
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
    
    def _get_whatsapp_service(self):
        if self.whatsapp_service is None:
            from bot.services.whatsapp_service import WhatsAppService
            self.whatsapp_service = WhatsAppService()
        return self.whatsapp_service

    # === Conversation State Management ===
    
    def _get_conversation_states(self) -> Tuple:
        """Get conversation state functions with fallback"""
        try:
            from bot.handlers.conversation_states import (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            )
            return (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            )
        except ImportError:
            logger.warning("Conversation states module not found, using fallback")
            return self._create_fallback_states()
    
    def _create_fallback_states(self) -> Tuple:
        """Create fallback state management functions"""
        user_states = {}
        appointment_data = {}
        conversation_context = {}
        user_language = {}
        
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
            return user_language.get(chat_id, 'swenglish')
        
        def set_user_language(chat_id, language):
            user_language[chat_id] = language
            
        return (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        )

    # === Platform Detection ===
    
    def _is_whatsapp_update(self, update: Dict) -> bool:
        """Check if this is a WhatsApp-style update"""
        if 'message' in update:
            chat_id = update['message'].get('chat', {}).get('id')
            return isinstance(chat_id, str) and chat_id.startswith('254')
        return False

    # === Main Update Handlers ===
    
    def handle_update(self, update: Dict):
        """Main handler for all updates - supports both Telegram and WhatsApp"""
        try:
            # Check if this is a WhatsApp-style update
            if self._is_whatsapp_update(update):
                # For WhatsApp, we need to handle it asynchronously
                asyncio.create_task(self.handle_whatsapp_message_async(update['message']))
                return
                
            logger.info(f"📨 Processing Telegram update")
            
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
            else:
                logger.warning(f"Unhandled update type")
        except Exception as e:
            logger.error(f"❌ Error handling update: {e}")

    async def handle_whatsapp_message_async(self, message: Dict):
        """Handle WhatsApp messages asynchronously"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            logger.info(f"📱 Processing WhatsApp message from {chat_id}: {text}")
            
            # Get conversation states
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            ) = self._get_conversation_states()
            
            # DEBUG: Log current state
            current_state = get_user_state(chat_id)
            logger.info(f"🔍 DEBUG: User {chat_id} state: {current_state}")
            
            # Detect and set language preference
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
            
            # Process the message based on current state
            response = await self._process_message_based_on_state(chat_id, text, current_state)
            
            # Send response via WhatsApp
            await self.send_whatsapp_response(chat_id, response)
            
            # Record conversation
            try:
                memory = self._get_memory()
                memory.record_conversation(chat_id, text, response)
            except Exception as e:
                logger.error(f"Error recording conversation: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error handling WhatsApp message: {e}")

    async def _process_message_based_on_state(self, chat_id: str, text: str, current_state: str) -> str:
        """Process message based on current conversation state"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        if current_state == ConversationState.CHOOSING_LANGUAGE:
            # Handle language selection in a way that returns response
            return await self._handle_language_selection_response(chat_id, text)
        
        elif current_state == ConversationState.AWAITING_PHONE:
            # Handle payment - this will send its own messages
            self.handle_payment_message(chat_id, text)
            return "Processing your payment information..."
        
        elif current_state in [ConversationState.APPOINTMENT_IN_PROGRESS, 
                              ConversationState.AWAITING_SERVICE,
                              ConversationState.AWAITING_TIME,
                              ConversationState.AWAITING_CONFIRMATION]:
            # Handle appointment conversation - this will send its own messages
            self.handle_appointment_conversation(chat_id, text, current_state)
            return "Processing your appointment..."
        
        elif text.startswith('/'):
            # Handle commands
            command_handler = self._get_command_handler()
            command_handler.handle_command(chat_id, text)
            return "Processing command..."
        
        else:
            # Handle natural language
            if self.is_appointment_intent(text):
                self.start_natural_appointment(chat_id, text)
                return "Starting appointment booking..."
            elif self.is_language_switch_request(text):
                self.offer_language_options(chat_id)
                return "Please choose your language preference..."
            else:
                return self.generate_cultural_response(chat_id, text)

    async def _handle_language_selection_response(self, chat_id: str, text: str) -> str:
        """Handle language selection and return appropriate response"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        text_lower = text.lower()
        
        if 'sheng' in text_lower or 'informal' in text_lower:
            set_user_language(chat_id, 'sheng')
            set_user_state(chat_id, ConversationState.IDLE)
            return "Poa msee! 😎 Sasa tuko on the same page. Unataka nini?"
        elif 'english' in text_lower or 'formal' in text_lower:
            set_user_language(chat_id, 'english')
            set_user_state(chat_id, ConversationState.IDLE)
            return "Perfect! I'll use English. How may I assist you today?"
        elif 'swenglish' in text_lower or 'swahili' in text_lower:
            set_user_language(chat_id, 'swenglish')
            set_user_state(chat_id, ConversationState.IDLE)
            return "Sawa! Tutazungumza Swenglish. Unataka nini? 😊"
        else:
            return "Please choose: Sheng, Swenglish, or English"

    def handle_message(self, message: Dict):
        """Handle incoming Telegram messages"""
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
        
        # DEBUG: Log current state
        current_state = get_user_state(chat_id)
        logger.info(f"🔍 DEBUG: User {chat_id} state: {current_state}")
        
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
        elif user_state == ConversationState.AWAITING_PHONE:
            self.handle_payment_message(chat_id, text)
        elif user_state != ConversationState.IDLE:
            self.handle_appointment_conversation(chat_id, text, user_state)
        elif text.startswith('/'):
            command_handler.handle_command(chat_id, text)
        else:
            # Check natural language intents
            if self.is_appointment_intent(text):
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

    # === Language Detection & Response Generation ===
    
    def detect_language_preference(self, text: str) -> str:
        """Detect user's language preference from their message"""
        text_lower = text.lower()
        
        # Sheng indicators
        sheng_words = ['mambo', 'sasa', 'niaje', 'msee', 'boss', 'vipi', 'poa', 'sawa', 'fiti', 'vibe']
        if any(word in text_lower for word in sheng_words):
            return 'sheng'
        
        # Swahili indicators
        swahili_words = ['habari', 'karibu', 'asante', 'tafadhali', 'unataka', 'nini', 'huduma', 'piga']
        if any(word in text_lower for word in swahili_words):
            return 'swenglish'
        
        # English indicators
        if re.search(r'\b(hello|hi|hey|book|appointment|service|price|please|thank)\b', text_lower):
            return 'english'
            
        return 'swenglish'  # Default

    def get_response(self, chat_id: str, response_type: str, **kwargs) -> str:
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

    def generate_cultural_response(self, chat_id: str, user_message: str) -> str:
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
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'mambo', 'niaje', 'sasa', 'habari', 'morning', 'afternoon']):
            return self.get_response(chat_id, 'greeting')
        
        # Service inquiries
        elif any(word in message_lower for word in ['service', 'huduma', 'nini', 'offer', 'do', 'available']):
            return self.get_service_options(chat_id)
        
        # Price inquiries
        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'bei', 'pesa', 'charge']):
            return self.get_pricing_info(chat_id)
        
        # Location inquiries
        elif any(word in message_lower for word in ['where', 'location', 'wapi', 'place', 'address', 'find']):
            return self.get_location_info(chat_id)
        
        # Booking intent
        elif self.is_appointment_intent(message_lower):
            return self.get_response(chat_id, 'booking_prompt')
        
        # Payment inquiries
        elif any(word in message_lower for word in ['pay', 'payment', 'mpesa', 'lipa', 'cash', 'deposit']):
            return self.get_payment_info(chat_id)
        
        # Thanks
        elif any(word in message_lower for word in ['thank', 'thanks', 'asante', 'shukran', 'appreciate']):
            return self.get_response(chat_id, 'thanks')
        
        # Default engaging response
        else:
            return self.get_engaging_fallback(chat_id, user_message)

    # === Response Templates ===
    
    def get_service_options(self, chat_id: str) -> str:
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

    def get_pricing_info(self, chat_id: str) -> str:
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

    def get_location_info(self, chat_id: str) -> str:
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

    def get_payment_info(self, chat_id: str) -> str:
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

    def get_engaging_fallback(self, chat_id: str, user_message: str) -> str:
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

    # === Language Switching ===
    
    def is_language_switch_request(self, text: str) -> bool:
        """Check if user wants to switch language"""
        language_words = ['english', 'swahili', 'sheng', 'language', 'lugha', 'zungumza', 'speak']
        return any(word in text.lower() for word in language_words)

    def offer_language_options(self, chat_id: str):
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

    def handle_language_selection(self, chat_id: str, text: str):
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

    # === Appointment Handling - IMPROVED ===
    
    def is_appointment_intent(self, text: str) -> bool:
        """Detect if user wants to book an appointment - IMPROVED"""
        text_lower = text.lower()
        
        appointment_keywords = [
            'book', 'appointment', 'schedule', 'reserve', 'miadi',
            'come in', 'visit', 'see you', 'available', 'free',
            'nikaweke', 'tengeneza', 'weka', 'ingia', 'nataka', 'i want',
            'need', 'would like', 'napenda', 'reservation', 'make appointment',
            'set appointment', 'create appointment', 'new appointment', 'booking'
        ]
        
        return any(keyword in text_lower for keyword in appointment_keywords)

    def start_natural_appointment(self, chat_id: str, user_message: str):
        """Start natural appointment conversation - IMPROVED"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            ) = self._get_conversation_states()
            
            # Extract service intent from message
            service_intent = self.extract_service_intent(user_message)
            
            # Initialize appointment data
            appointment_data = {
                'service_intent': service_intent,
                'step': 'service_selection'
            }
            
            set_appointment_data(chat_id, appointment_data)
            set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
            
            telegram = self._get_telegram()
            
            if service_intent:
                # If service is clear, move to time selection
                self._ask_for_appointment_time(chat_id, service_intent)
            else:
                # Ask about service preference
                telegram.send_message(chat_id, self.get_response(chat_id, 'service_question'))
                set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
            
            logger.info(f"🔍 DEBUG: Started appointment flow for {chat_id}, service_intent: {service_intent}")
            
        except Exception as e:
            logger.error(f"❌ Error starting natural appointment: {e}")

    def extract_service_intent(self, text: str) -> Optional[str]:
        """Extract service intent from natural language - IMPROVED"""
        text_lower = text.lower()
        
        # Expanded service mapping with better matching
        for service, keywords in self.service_mapping.items():
            for keyword in keywords:
                if keyword in text_lower:
                    logger.info(f"🔍 DEBUG: Extracted service '{service}' from '{text}' using keyword '{keyword}'")
                    return service
        
        logger.info(f"🔍 DEBUG: No service extracted from '{text}'")
        return None

    def handle_appointment_conversation(self, chat_id: str, text: str, user_state: str):
        """Handle appointment conversation flow - IMPROVED"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        appointment_data = get_appointment_data(chat_id)
        
        logger.info(f"🔍 DEBUG: Handling appointment conversation - state: {user_state}, data: {appointment_data}")
        
        if user_state == ConversationState.APPOINTMENT_IN_PROGRESS:
            self.continue_appointment_flow(chat_id, text, appointment_data)
        elif user_state == ConversationState.AWAITING_SERVICE:
            self._handle_service_selection(chat_id, text)
        elif user_state == ConversationState.AWAITING_TIME:
            self._handle_time_selection(chat_id, text)
        elif user_state == ConversationState.AWAITING_CONFIRMATION:
            self.handle_confirmation(chat_id, text)
        else:
            # Fallback: reset conversation
            logger.warning(f"🔍 DEBUG: Unknown state {user_state}, resetting conversation")
            set_user_state(chat_id, ConversationState.IDLE)
            telegram.send_message(chat_id, "Let's start over. How can I help you?")

    def _handle_service_selection(self, chat_id: str, text: str):
        """Handle service selection from user"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        service = self.extract_service_intent(text)
        
        if service:
            appointment_data = get_appointment_data(chat_id) or {}
            appointment_data['service'] = service
            appointment_data['price'] = self.service_prices[service]['default']
            set_appointment_data(chat_id, appointment_data)
            
            self._ask_for_appointment_time(chat_id, service)
        else:
            telegram.send_message(chat_id, "I'm not sure which service you want. Please specify: hair, nails, facial, makeup, or massage?")

    def _ask_for_appointment_time(self, chat_id: str, service: str):
        """Ask user for appointment time"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        time_question = self.get_response(chat_id, 'time_question', service=service.capitalize())
        telegram.send_message(chat_id, time_question)
        set_user_state(chat_id, ConversationState.AWAITING_TIME)

    def _handle_time_selection(self, chat_id: str, text: str):
        """Handle time selection from user"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        appointment_data = get_appointment_data(chat_id)
        if appointment_data:
            appointment_data['preferred_time'] = text
            set_appointment_data(chat_id, appointment_data)
            set_user_state(chat_id, ConversationState.AWAITING_CONFIRMATION)
            
            # Show confirmation
            service = appointment_data['service']
            price = appointment_data['price']
            
            confirmation_msg = f"""
✅ *Appointment Summary:*

*Service:* {service.capitalize()}
*Time:* {text}
*Price:* KES {price}

*Is this correct?* Reply 'yes' to confirm or 'no' to change.
            """
            telegram.send_message(chat_id, confirmation_msg)

    def continue_appointment_flow(self, chat_id: str, text: str, appointment_data: Dict):
        """Continue the appointment booking flow - IMPROVED"""
        # This method now handles the initial flow when service intent might be in the message
        service = self.extract_service_intent(text)
        
        if service:
            # If service is detected in this message, use it
            appointment_data = appointment_data or {}
            appointment_data['service'] = service
            appointment_data['price'] = self.service_prices[service]['default']
            self._ask_for_appointment_time(chat_id, service)
        else:
            # No service detected, ask for it specifically
            self._get_telegram().send_message(chat_id, self.get_response(chat_id, 'service_question'))
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context,
                get_user_language, set_user_language
            ) = self._get_conversation_states()
            set_user_state(chat_id, ConversationState.AWAITING_SERVICE)

    def handle_confirmation(self, chat_id: str, text: str):
        """Handle appointment confirmation - IMPROVED"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        text_lower = text.lower()
        
        if text_lower in ['yes', 'y', 'sawa', 'ndio', 'confirm', 'correct', 'ok', 'proceed']:
            appointment_data = get_appointment_data(chat_id)
            if appointment_data:
                service = appointment_data['service']
                price = appointment_data['price']
                
                # Move to payment
                set_user_state(chat_id, ConversationState.AWAITING_PHONE)
                
                payment_msg = f"""
🎉 *Appointment Confirmed!*

*Service:* {service.capitalize()}
*Time:* {appointment_data.get('preferred_time', 'To be confirmed')}
*Amount:* KES {price}

{self.get_response(chat_id, 'payment_prompt')}
                """
                telegram.send_message(chat_id, payment_msg)
                
                logger.info(f"🔍 DEBUG: Appointment confirmed for {chat_id}, moving to payment")
            else:
                telegram.send_message(chat_id, "Sorry, I lost track of your appointment. Let's start over.")
                set_user_state(chat_id, ConversationState.IDLE)
                
        elif text_lower in ['no', 'n', 'hapana', 'change', 'cancel']:
            # Restart appointment process
            set_user_state(chat_id, ConversationState.IDLE)
            clear_appointment_data(chat_id)
            telegram.send_message(chat_id, "No problem! Let's start over. What service would you like?")
        else:
            telegram.send_message(chat_id, "Please reply 'yes' to confirm or 'no' to change your appointment.")

    def handle_payment_message(self, chat_id: str, text: str):
        """Handle payment information"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        # Extract phone number (simple validation)
        phone_match = re.search(r'(?:254|\+254|0)?(7\d{8})', text.replace(' ', ''))
        
        if phone_match:
            phone_number = f"254{phone_match.group(1)}"
            appointment_data = get_appointment_data(chat_id)
            
            try:
                payment_handler = self._get_payment_handler()
                result = payment_handler.initiate_mpesa_payment(
                    phone_number, 
                    appointment_data['price'],
                    f"Beauty service: {appointment_data['service']}"
                )
                
                if result.get('success'):
                    telegram.send_message(chat_id, self.get_response(chat_id, 'confirmation'))
                    
                    # Record appointment
                    try:
                        memory = self._get_memory()
                        memory.record_appointment(
                            chat_id,
                            appointment_data['service'],
                            appointment_data['preferred_time'],
                            appointment_data['price'],
                            'pending'
                        )
                    except Exception as e:
                        logger.error(f"Error recording appointment: {e}")
                    
                else:
                    telegram.send_message(chat_id, "Sorry, payment failed. Please try again or contact us.")
                    
            except Exception as e:
                logger.error(f"Payment error: {e}")
                telegram.send_message(chat_id, "Payment service unavailable. Please contact us directly.")
            
            # Reset conversation
            set_user_state(chat_id, ConversationState.IDLE)
            clear_appointment_data(chat_id)
            
        else:
            telegram.send_message(chat_id, "Please provide a valid Kenyan phone number (e.g., 0712345678)")

    # === Callback Handler ===
    
    def handle_callback(self, callback_query: Dict):
        """Handle callback queries from inline keyboards"""
        try:
            chat_id = callback_query['message']['chat']['id']
            data = callback_query['data']
            
            logger.info(f"Processing callback from {chat_id}: {data}")
            
            telegram = self._get_telegram()
            
            if data.startswith('service_'):
                service = data.replace('service_', '')
                self.handle_service_selection(chat_id, service)
            elif data == 'book_appointment':
                self.start_natural_appointment(chat_id, "book appointment")
            elif data == 'ask_prices':
                telegram.send_message(chat_id, self.get_pricing_info(chat_id))
            elif data == 'location':
                telegram.send_message(chat_id, self.get_location_info(chat_id))
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")

    def handle_service_selection(self, chat_id: str, service: str):
        """Handle service selection from inline keyboard"""
        telegram = self._get_telegram()
        
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        price = self.service_prices.get(service, {}).get('default', 1000)
        
        set_appointment_data(chat_id, {
            'service': service,
            'price': price
        })
        set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
        
        self._ask_for_appointment_time(chat_id, service)

    # === WhatsApp Integration ===
    
    async def send_whatsapp_response(self, phone_number: str, response_text: str):
        """Send response via WhatsApp"""
        try:
            whatsapp = self._get_whatsapp_service()
            await whatsapp.send_message(phone_number, response_text)
            logger.info(f"✅ WhatsApp response sent to {phone_number}")
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp response: {e}")

    # === Webhook Handler for WhatsApp ===
    
    async def handle_whatsapp_webhook(self, webhook_data: Dict) -> Dict:
        """Handle WhatsApp webhook data directly"""
        try:
            logger.info(f"📱 Received WhatsApp webhook data")
            
            # Extract message from WhatsApp webhook format
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return {"status": "ignored", "reason": "No messages"}
            
            message = messages[0]
            from_number = message.get('from')
            text = message.get('text', {}).get('body', '')
            
            if not text:
                return {"status": "ignored", "reason": "No text content"}
            
            # Create WhatsApp-style message format
            whatsapp_message = {
                'chat': {'id': from_number},
                'text': text,
                'from': {'id': from_number}
            }
            
            # Process the message asynchronously
            await self.handle_whatsapp_message_async(whatsapp_message)
            
            return {"status": "processed", "user": from_number, "message": text}
            
        except Exception as e:
            logger.error(f"❌ Error handling WhatsApp webhook: {e}")
            return {"status": "error", "error": str(e)}