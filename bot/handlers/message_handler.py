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
    AWAITING_SERVICE = "awaiting_service"
    AWAITING_TIME = "awaiting_time"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_PHONE = "awaiting_phone"
    CHOOSING_LANGUAGE = "choosing_language"

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
                'time_question': "Sawa! {service} it is! 💅\n\nWhen unataka kuingia? (e.g., 'kesho 2pm', 'Friday morning')",
                'confirmation': "Poa! Tumeconfirm appointment yako. Tutakuona kwa salon! 🔥",
                'payment_prompt': "To lock your slot, tafadhali tuma namba yako ya simu kwa M-Pesa STK Push...",
                'thanks': "Asante mzee! Uko solid. Karibu tena anytime! 🙌",
                'appointment_booked': "Booked! 💅 Appointment yako for {service} imesetiwa {time}. STK Push imetuma kwa {phone}!"
            },
            'swenglish': {
                'greeting': [
                    "Habari yako! Welcome to Frank Beauty Salon. How can we make you beautiful today? 💅",
                    "Karibu sana! We're excited to serve you. What treatment would you like? ✨",
                    "Jambo! Welcome to Frank Beauty Spot. Tuko hapa kukupatia the best beauty experience. 😊"
                ],
                'booking_prompt': "Would you like to book an appointment? Tafadhali tell me what service unataka.",
                'service_question': "Which service ungependa? We have haircut, manicure, pedicure, facial, na makeup.",
                'time_question': "Nice! {service} it is! 💅\n\nWhen would you like to come? (e.g., 'tomorrow 2pm', 'Friday morning')",
                'confirmation': "Perfect! Tumeconfirm your appointment. Tutakuona on the scheduled date! ✅",
                'payment_prompt': "Tafadhali provide your phone number for M-Pesa STK Push payment...",
                'thanks': "Asante sana for choosing us! We look forward to serving you. 🎉",
                'appointment_booked': "Booked! 💅 Your {service} appointment is set for {time}. STK Push sent to {phone}!"
            },
            'english': {
                'greeting': [
                    "Hello! Welcome to Frank Beauty Salon! How may I assist you today? 💇‍♀️",
                    "Good day! Ready for your beauty transformation? What can I help you with? ✨",
                    "Welcome to Frank Beauty Spot! We're here to make you feel fabulous. 😊"
                ],
                'booking_prompt': "Would you like to schedule an appointment? Please tell me what service you're interested in.",
                'service_question': "What service would you like? We offer haircuts, manicures, facials, and makeup services.",
                'time_question': "Great choice! {service} it is! 💅\n\nWhen would you like to come? (e.g., 'tomorrow 2pm', 'Friday morning')",
                'confirmation': "Excellent! Your appointment has been confirmed. We'll see you then! ✅",
                'payment_prompt': "Please provide your phone number for M-Pesa STK Push payment...",
                'thanks': "Thank you for choosing Frank Beauty Salon! We appreciate your business. 🎉",
                'appointment_booked': "Booked! 💅 Your {service} appointment is confirmed for {time}. STK Push sent to {phone}!"
            }
        }
        
        # Expanded service mapping for better detection
        self.service_mapping = {
            'hair': ['hair', 'nywele', 'cut', 'trim', 'style', 'blow', 'braid', 'weave', 'haircut', 'styling', 'blowout', 'hair do', 'hairdo'],
            'nails': ['nail', 'manicure', 'pedicure', 'kucha', 'polish', 'gel', 'nails', 'manicure', 'pedicure', 'nail care'],
            'face': ['facial', 'face', 'uso', 'skin', 'cleanse', 'treatment', 'facial', 'skincare', 'skin care'],
            'makeup': ['makeup', 'beat', 'glam', 'foundation', 'lipstick', 'eye', 'make up', 'make-up', 'bridal', 'makeover'],
            'massage': ['massage', 'massaji', 'relax', 'spa', 'therapy', 'body massage', 'massage therapy']
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
    
    def _get_memory(self):
        if self.memory is None:
            from bot.services.customer_memory import CustomerMemory
            self.memory = CustomerMemory()
        return self.memory
    
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
        """Handle WhatsApp messages asynchronously - FIXED VERSION"""
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
            
            # Process message based on state - FIXED: This now properly handles the flow
            response = await self._process_whatsapp_message(chat_id, text, current_state)
            
            # Send response via WhatsApp
            if response:
                await self.send_whatsapp_response(chat_id, response)
            
            # Record conversation
            try:
                memory = self._get_memory()
                memory.record_conversation(chat_id, text, response or "No response")
            except Exception as e:
                logger.error(f"Error recording conversation: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error handling WhatsApp message: {e}")

    async def _process_whatsapp_message(self, chat_id: str, text: str, current_state: str) -> Optional[str]:
        """Process WhatsApp message and return appropriate response - FIXED"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        logger.info(f"🔍 DEBUG: Processing message '{text}' in state '{current_state}'")
        
        if current_state == ConversationState.CHOOSING_LANGUAGE:
            return await self._handle_language_selection_response(chat_id, text)
        
        elif current_state == ConversationState.AWAITING_PHONE:
            # Handle payment - this sends its own WhatsApp messages
            await self._handle_payment_whatsapp(chat_id, text)
            return None
        
        elif current_state in [ConversationState.APPOINTMENT_IN_PROGRESS, 
                              ConversationState.AWAITING_SERVICE,
                              ConversationState.AWAITING_TIME,
                              ConversationState.AWAITING_CONFIRMATION]:
            # Handle appointment conversation - this sends its own WhatsApp messages
            await self._handle_appointment_whatsapp(chat_id, text, current_state)
            return None
        
        elif text.startswith('/'):
            # Handle commands
            command_handler = self._get_command_handler()
            command_handler.handle_command(chat_id, text)
            return "Processing command..."
        
        else:
            # Handle natural language
            if self.is_appointment_intent(text):
                # Start booking flow - this sends WhatsApp messages directly
                await self._start_booking_whatsapp(chat_id, text)
                return None
            elif self.is_language_switch_request(text):
                self.offer_language_options_whatsapp(chat_id)
                return None
            else:
                return self.generate_cultural_response(chat_id, text)

    async def _start_booking_whatsapp(self, chat_id: str, user_message: str):
        """Start booking flow for WhatsApp - sends messages directly"""
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
                'step': 'started'
            }
            
            set_appointment_data(chat_id, appointment_data)
            
            if service_intent:
                # If service is clear, move to time selection
                set_user_state(chat_id, ConversationState.AWAITING_TIME)
                time_question = self.get_response(chat_id, 'time_question', service=service_intent.capitalize())
                await self.send_whatsapp_response(chat_id, time_question)
                logger.info(f"🔍 DEBUG: Started booking with service: {service_intent}")
            else:
                # Ask about service preference
                set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
                service_question = self.get_response(chat_id, 'service_question')
                await self.send_whatsapp_response(chat_id, service_question)
                logger.info(f"🔍 DEBUG: Started booking - asking for service")
            
        except Exception as e:
            logger.error(f"❌ Error starting booking: {e}")
            await self.send_whatsapp_response(chat_id, "Sorry, there was an error starting your booking. Please try again.")

    async def _handle_appointment_whatsapp(self, chat_id: str, text: str, current_state: str):
        """Handle appointment conversation for WhatsApp - sends messages directly"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        logger.info(f"🔍 DEBUG: Handling appointment - state: {current_state}, message: '{text}'")
        
        if current_state == ConversationState.AWAITING_SERVICE:
            await self._handle_service_selection_whatsapp(chat_id, text)
        
        elif current_state == ConversationState.AWAITING_TIME:
            await self._handle_time_selection_whatsapp(chat_id, text)
        
        elif current_state == ConversationState.AWAITING_CONFIRMATION:
            await self._handle_confirmation_whatsapp(chat_id, text)

    async def _handle_service_selection_whatsapp(self, chat_id: str, text: str):
        """Handle service selection for WhatsApp"""
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
            
            set_user_state(chat_id, ConversationState.AWAITING_TIME)
            time_question = self.get_response(chat_id, 'time_question', service=service.capitalize())
            await self.send_whatsapp_response(chat_id, time_question)
            logger.info(f"🔍 DEBUG: Service selected: {service}")
        else:
            await self.send_whatsapp_response(chat_id, "I'm not sure which service you want. Please specify: hair, nails, facial, makeup, or massage?")

    async def _handle_time_selection_whatsapp(self, chat_id: str, text: str):
        """Handle time selection for WhatsApp"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        appointment_data = get_appointment_data(chat_id)
        if appointment_data and appointment_data.get('service'):
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
            await self.send_whatsapp_response(chat_id, confirmation_msg)
            logger.info(f"🔍 DEBUG: Time selected: {text}")
        else:
            await self.send_whatsapp_response(chat_id, "I lost track of your service selection. Let's start over.")
            set_user_state(chat_id, ConversationState.IDLE)

    async def _handle_confirmation_whatsapp(self, chat_id: str, text: str):
        """Handle confirmation for WhatsApp"""
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
                set_user_state(chat_id, ConversationState.AWAITING_PHONE)
                payment_prompt = self.get_response(chat_id, 'payment_prompt')
                await self.send_whatsapp_response(chat_id, payment_prompt)
                logger.info(f"🔍 DEBUG: Appointment confirmed, awaiting phone")
            else:
                await self.send_whatsapp_response(chat_id, "Sorry, I lost track of your appointment. Let's start over.")
                set_user_state(chat_id, ConversationState.IDLE)
                
        elif text_lower in ['no', 'n', 'hapana', 'change', 'cancel']:
            set_user_state(chat_id, ConversationState.IDLE)
            clear_appointment_data(chat_id)
            await self.send_whatsapp_response(chat_id, "No problem! Let's start over. What service would you like?")
        else:
            await self.send_whatsapp_response(chat_id, "Please reply 'yes' to confirm or 'no' to change your appointment.")

    async def _handle_payment_whatsapp(self, chat_id: str, text: str):
        """Handle payment for WhatsApp with STK Push"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        # Extract phone number
        phone_match = re.search(r'(?:254|\+254|0)?(7\d{8})', text.replace(' ', ''))
        
        if phone_match:
            phone_number = f"254{phone_match.group(1)}"
            appointment_data = get_appointment_data(chat_id)
            
            if appointment_data:
                try:
                    payment_handler = self._get_payment_handler()
                    
                    # Initiate STK Push
                    result = payment_handler.initiate_mpesa_payment(
                        phone_number, 
                        appointment_data['price'],
                        f"Frank Beauty: {appointment_data['service']}"
                    )
                    
                    if result.get('success'):
                        # Record appointment
                        try:
                            memory = self._get_memory()
                            memory.record_appointment(
                                chat_id,
                                appointment_data['service'],
                                appointment_data.get('preferred_time', 'To be confirmed'),
                                appointment_data['price'],
                                'pending'
                            )
                        except Exception as e:
                            logger.error(f"Error recording appointment: {e}")
                        
                        # Send success message
                        booked_msg = self.get_response(chat_id, 'appointment_booked',
                                                     service=appointment_data['service'].capitalize(),
                                                     time=appointment_data.get('preferred_time', 'soon'),
                                                     phone=phone_number)
                        await self.send_whatsapp_response(chat_id, booked_msg)
                        
                        # Also send confirmation
                        confirm_msg = self.get_response(chat_id, 'confirmation')
                        await self.send_whatsapp_response(chat_id, confirm_msg)
                        
                        logger.info(f"🔍 DEBUG: STK Push sent to {phone_number} for {appointment_data['service']}")
                    
                    else:
                        error_msg = "Sorry, STK Push failed. Please check your phone number or try again later."
                        await self.send_whatsapp_response(chat_id, error_msg)
                        
                except Exception as e:
                    logger.error(f"Payment error: {e}")
                    error_msg = "Payment service temporarily unavailable. Please contact us directly."
                    await self.send_whatsapp_response(chat_id, error_msg)
                
                # Reset conversation regardless of payment result
                set_user_state(chat_id, ConversationState.IDLE)
                clear_appointment_data(chat_id)
                
            else:
                await self.send_whatsapp_response(chat_id, "Sorry, I lost track of your appointment details. Let's start over.")
                set_user_state(chat_id, ConversationState.IDLE)
        else:
            await self.send_whatsapp_response(chat_id, "Please provide a valid Kenyan phone number (e.g., 0712345678)")

    def offer_language_options_whatsapp(self, chat_id: str):
        """Offer language options for WhatsApp"""
        asyncio.create_task(self._send_language_options_whatsapp(chat_id))

    async def _send_language_options_whatsapp(self, chat_id: str):
        """Send language options via WhatsApp"""
        (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context,
            get_user_language, set_user_language
        ) = self._get_conversation_states()
        
        message = """
🗣️ *Choose your preferred language:*

• *Sheng* - For the cool, informal vibe 😎
• *Swenglish* - Mix of Swahili & English 🇰🇪  
• *English* - Formal and professional 💼

*Reply with your choice!*
        """
        
        await self.send_whatsapp_response(chat_id, message)
        set_user_state(chat_id, ConversationState.CHOOSING_LANGUAGE)

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

    # === Core Business Logic (Keep existing methods but fix key issues) ===
    
    def is_appointment_intent(self, text: str) -> bool:
        """Detect if user wants to book an appointment - IMPROVED"""
        text_lower = text.lower()
        
        appointment_keywords = [
            'book', 'appointment', 'schedule', 'reserve', 'miadi',
            'come in', 'visit', 'see you', 'available', 'free',
            'nikaweke', 'tengeneza', 'weka', 'ingia', 'nataka', 'i want',
            'need', 'would like', 'napenda', 'reservation', 'make appointment',
            'set appointment', 'create appointment', 'new appointment', 'booking',
            'weka appointment', 'tengeneza miadi', 'ingia salon'
        ]
        
        return any(keyword in text_lower for keyword in appointment_keywords)

    def extract_service_intent(self, text: str) -> Optional[str]:
        """Extract service intent from natural language - IMPROVED"""
        text_lower = text.lower()
        
        # Check for exact matches first
        for service, keywords in self.service_mapping.items():
            for keyword in keywords:
                # Use word boundaries for better matching
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    logger.info(f"🔍 DEBUG: Extracted service '{service}' from '{text}'")
                    return service
        
        logger.info(f"🔍 DEBUG: No service extracted from '{text}'")
        return None

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

    # === Response Templates (Keep existing) ===
    def get_service_options(self, chat_id: str) -> str:
        """Get service options in user's preferred language"""
        language = self._get_conversation_states()[-2](chat_id)
        
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

    def is_language_switch_request(self, text: str) -> bool:
        """Check if user wants to switch language"""
        language_words = ['english', 'swahili', 'sheng', 'language', 'lugha', 'zungumza', 'speak']
        return any(word in text.lower() for word in language_words)

    def _is_whatsapp_update(self, update: Dict) -> bool:
        """Check if this is a WhatsApp-style update"""
        if 'message' in update:
            chat_id = update['message'].get('chat', {}).get('id')
            return isinstance(chat_id, str) and chat_id.startswith('254')
        return False

    async def send_whatsapp_response(self, phone_number: str, response_text: str):
        """Send response via WhatsApp"""
        try:
            whatsapp = self._get_whatsapp_service()
            await whatsapp.send_message(phone_number, response_text)
            logger.info(f"✅ WhatsApp response sent to {phone_number}")
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp response: {e}")

    # === Keep existing Telegram methods but ensure they work ===
    def handle_message(self, message: Dict):
        """Handle incoming Telegram messages"""
        # ... [Keep your existing Telegram handling code]
        pass

    def handle_callback(self, callback_query: Dict):
        """Handle callback queries from inline keyboards"""
        # ... [Keep your existing callback handling code]
        pass

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