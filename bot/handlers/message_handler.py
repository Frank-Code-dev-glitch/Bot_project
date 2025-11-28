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

class MessageHandler:
    def __init__(self):
        # Lazy imports to avoid circular imports
        self.command_handler = None
        self.ai_service = None
        self.memory = None
        self.knowledge = None
        self.telegram = None
        self.payment_handler = None
        logger.info("✅ MessageHandler initialized - Components will be lazy-loaded")
    
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
            # Fallback implementation if conversation_states is not available
            logger.warning("Conversation states module not found, using fallback")
            return self._create_fallback_states()
    
    def _create_fallback_states(self):
        """Create fallback state management functions"""
        user_states = {}
        appointment_data = {}
        conversation_context = {}
        
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
        
        return (
            get_user_state, set_user_state, clear_user_state,
            get_appointment_data, set_appointment_data, clear_appointment_data,
            get_conversation_context, set_conversation_context
        )
    
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
        """Handle incoming messages"""
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
            get_conversation_context, set_conversation_context
        ) = self._get_conversation_states()
        
        # Record customer interaction
        try:
            memory = self._get_memory()
            memory.remember_customer(chat_id)
        except Exception as e:
            logger.error(f"Error remembering customer: {e}")
        
        # Check user state first
        user_state = get_user_state(chat_id)
        
        if user_state != ConversationState.IDLE:
            self.handle_appointment_conversation(chat_id, text, user_state)
        elif text.startswith('/'):
            command_handler.handle_command(chat_id, text)
        else:
            # Check if this is payment context
            appointment_data = get_appointment_data(chat_id)
            if appointment_data and appointment_data.get('awaiting_phone'):
                self.handle_payment_message(chat_id, text)
            elif self.is_appointment_intent(text):
                self.start_smart_appointment(chat_id, text)
            else:
                # Use AI for other messages
                response = self.generate_enhanced_response(chat_id, text)
                
                # Record the conversation
                try:
                    memory = self._get_memory()
                    memory.record_conversation(chat_id, text, response)
                except Exception as e:
                    logger.error(f"Error recording conversation: {e}")
                
                telegram.send_message(chat_id, response)
    
    def generate_enhanced_response(self, chat_id, user_message):
        """Generate AI response with customer context"""
        try:
            # Get customer context
            memory = self._get_memory()
            customer_context = memory.get_customer_context(chat_id)
            
            # Get relevant salon knowledge
            knowledge = self._get_knowledge()
            salon_context = knowledge.get_context_for_query(user_message)
            
            # Generate personalized response
            ai_service = self._get_ai_service()
            response = ai_service.generate_enhanced_response(
                user_message, 
                customer_context=customer_context,
                salon_context=salon_context
            )
            
            logger.info(f"Generated response for {chat_id}: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Enhanced response error: {e}")
            return self._get_fallback_response(user_message)
    
    def _get_fallback_response(self, user_message):
        """Fallback response when AI service fails"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'niaje', 'mambo', 'sasa']):
            responses = [
                "Mambo! Niaje? Karibu Frank Beauty Spot! 😊 Unataka kujua bei, kuweka appointment, au nini?",
                "Sasa! Niko hapa kukusaidia! 💅 Unapenda kujua nini leo?",
                "Hey there! Welcome to Frank Beauty Spot! How can I help you today? 😊"
            ]
            return random.choice(responses)
        
        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'bei']):
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
        
        elif any(word in message_lower for word in ['book', 'appointment', 'miadi', 'weka']):
            return "Poa! Naweza kukusaidia kuweka appointment. 💅 Sema tu service unayotaka na time ungependa kuja!"
        
        elif any(word in message_lower for word in ['service', 'services', 'huduma']):
            return """
💇‍♀️ *Our Services:*
• Haircut & Styling
• Hair Coloring  
• Hair Treatment
• Manicure & Pedicure
• Facial Treatments
• Makeup Services

*Book now:* Just tell me what you'd like! 😊
            """
        
        elif any(word in message_lower for word in ['location', 'where', 'wapi', 'place']):
            return """
📍 *Frank Beauty Spot*
Tom Mboya Street, Nairobi CBD

*Hours:*
Mon-Fri: 8am - 7pm
Sat: 9am - 6pm  
Sun: 10am - 4pm

*Come visit us!* 🎉
            """
        
        else:
            responses = [
                "Niko hapa kukusaidia! 💅 Unataka kuweka appointment, kuuliza bei, au kujua services zetu?",
                "I'd love to help! 😊 You can ask me about prices, book an appointment, or learn about our services!",
                "Karibu! How can I assist you today? 💅 You can book appointments, check prices, or ask about our services!"
            ]
            return random.choice(responses)
    
    def handle_payment_message(self, chat_id, text):
        """Handle payment-related messages"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            appointment_data = get_appointment_data(chat_id)
            
            if appointment_data.get('awaiting_phone'):
                service_type = appointment_data.get('service_type', 'deposit')
                amount = appointment_data.get('amount', 500)
                
                payment_handler = self._get_payment_handler()
                payment_handler.process_phone_number(chat_id, text, service_type, amount)
                
                set_appointment_data(chat_id, {'awaiting_phone': False})
        except Exception as e:
            logger.error(f"Error handling payment message: {e}")
    
    def handle_callback(self, callback_query):
        """Handle callback queries"""
        try:
            chat_id = callback_query['message']['chat']['id']
            data = callback_query['data']
            callback_query_id = callback_query['id']
            
            logger.info(f"🎯 CALLBACK RECEIVED - Chat: {chat_id}, Data: '{data}'")
            
            telegram = self._get_telegram()
            telegram.answer_callback_query(callback_query_id)
            
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            if data == "confirm_appointment":
                appointment = get_appointment_data(chat_id)
                if appointment:
                    self.complete_appointment_booking(chat_id, appointment)
                else:
                    telegram.send_message(chat_id, "❌ Sorry, appointment details not found.")
                    clear_user_state(chat_id)
            
            elif data == "modify_appointment":
                telegram.send_message(chat_id, "No problem! What would you like to change?")
                set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
            
            elif data == "cancel_appointment":
                telegram.send_message(chat_id, "Okay, cancelled! Let me know if you change your mind! 😊")
                clear_user_state(chat_id)
                clear_appointment_data(chat_id)
            
            elif data.startswith('mpesa_') or data.startswith('cash_') or data.startswith('pay_'):
                payment_handler = self._get_payment_handler()
                
                if data.startswith('mpesa_stk_'):
                    parts = data.split('_')
                    service_type = parts[2] if len(parts) > 2 else 'haircut'
                    amount = int(parts[3]) if len(parts) > 3 else 500
                    payment_handler.initiate_mpesa_checkout(chat_id, service_type, amount)
                
                elif data.startswith('mpesa_manual_'):
                    service_type = data.split('_')[2] if len(data.split('_')) > 2 else 'haircut'
                    payment_handler.show_manual_mpesa_instructions(chat_id, service_type)
                
                elif data.startswith('cash_'):
                    service_type = data.split('_')[1] if len(data.split('_')) > 1 else 'haircut'
                    payment_handler.confirm_cash_payment(chat_id, service_type)
            
            elif data == 'back_to_menu':
                telegram.send_message(chat_id, "🏠 Back to main menu! How can I help you?")
                clear_user_state(chat_id)
                clear_appointment_data(chat_id)
            
            else:
                logger.warning(f"⚠️ Unknown callback: '{data}'")
                telegram.send_message(chat_id, "❌ Sorry, I didn't understand that action.")
                
        except Exception as e:
            logger.error(f"❌ Error handling callback: {e}")
    
    def is_appointment_intent(self, text):
        """Detect if user wants to book an appointment"""
        appointment_keywords = [
            'book', 'appointment', 'schedule', 'reserve', 'miadi',
            'come in', 'visit', 'see you', 'available', 'free',
            'nikaweke', 'tengeneza', 'weka', 'ingia'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in appointment_keywords)
    
    def start_smart_appointment(self, chat_id, user_message):
        """Start appointment booking"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            set_appointment_data(chat_id, {})
            set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
            
            # Simple booking prompt
            prompt = """
🎉 *Let's Book Your Appointment!* 

Tell me what service you'd like:
• Haircut
• Manicure/Pedicure  
• Facial
• Makeup
• Hair Color

Or just say what you have in mind! 💅
            """
            
            telegram = self._get_telegram()
            telegram.send_message(chat_id, prompt)
            
        except Exception as e:
            logger.error(f"Error starting appointment: {e}")
    
    def handle_appointment_conversation(self, chat_id, text, user_state):
        """Handle appointment conversation"""
        try:
            if user_state == ConversationState.APPOINTMENT_IN_PROGRESS:
                self.continue_appointment_flow(chat_id, text)
            elif user_state == ConversationState.AWAITING_CONFIRMATION:
                # Handle text responses during confirmation
                if text.lower() in ['yes', 'confirm', 'book it', 'ndio']:
                    (
                        get_user_state, set_user_state, clear_user_state,
                        get_appointment_data, set_appointment_data, clear_appointment_data,
                        get_conversation_context, set_conversation_context
                    ) = self._get_conversation_states()
                    
                    appointment = get_appointment_data(chat_id)
                    self.complete_appointment_booking(chat_id, appointment)
                elif text.lower() in ['no', 'change', 'modify']:
                    telegram = self._get_telegram()
                    telegram.send_message(chat_id, "No problem! What would you like to change?")
                    
                    (
                        get_user_state, set_user_state, clear_user_state,
                        get_appointment_data, set_appointment_data, clear_appointment_data,
                        get_conversation_context, set_conversation_context
                    ) = self._get_conversation_states()
                    
                    set_user_state(chat_id, ConversationState.APPOINTMENT_IN_PROGRESS)
                else:
                    self.continue_appointment_flow(chat_id, text)
        except Exception as e:
            logger.error(f"Appointment conversation error: {e}")
            telegram = self._get_telegram()
            telegram.send_message(chat_id, "Sorry, there was an error. Let's start over!")
    
    def continue_appointment_flow(self, chat_id, user_input):
        """Continue appointment flow"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            appointment = get_appointment_data(chat_id) or {}
            
            # Extract service from input
            service = self.extract_service(user_input)
            if service:
                appointment['service'] = service
            
            set_appointment_data(chat_id, appointment)
            
            # If we have a service, request confirmation
            if appointment.get('service'):
                self.request_confirmation(chat_id, appointment)
            else:
                # Ask for service
                telegram = self._get_telegram()
                telegram.send_message(chat_id, "What service would you like? 💅")
                
        except Exception as e:
            logger.error(f"Error in appointment flow: {e}")
    
    def extract_service(self, text):
        """Extract service type from text"""
        service_keywords = {
            'haircut': ['haircut', 'cut', 'trim', 'nywele'],
            'manicure': ['manicure', 'nails', 'kucha'],
            'pedicure': ['pedicure', 'feet', 'miguu'],
            'facial': ['facial', 'face', 'uso'],
            'makeup': ['makeup', 'beat'],
            'treatment': ['treatment', 'tiba']
        }
        
        text_lower = text.lower()
        for service, keywords in service_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return service
        return None
    
    def request_confirmation(self, chat_id, appointment):
        """Request appointment confirmation"""
        try:
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            summary = f"""
✅ *Appointment Summary:*

💅 *Service:* {appointment.get('service', 'Not specified')}

Does this look good? 😊
            """
            
            buttons = [
                [{"text": "✅ Yes, Book It!", "callback_data": "confirm_appointment"}],
                [{"text": "🔄 Change", "callback_data": "modify_appointment"}],
                [{"text": "❌ Cancel", "callback_data": "cancel_appointment"}]
            ]
            
            telegram = self._get_telegram()
            telegram.send_message_with_buttons(chat_id, summary, buttons)
            set_user_state(chat_id, ConversationState.AWAITING_CONFIRMATION)
            
        except Exception as e:
            logger.error(f"Error requesting confirmation: {e}")
    
    def complete_appointment_booking(self, chat_id, appointment):
        """Complete appointment booking"""
        try:
            logger.info(f"🎯 Completing booking for {chat_id}")
            
            telegram = self._get_telegram()
            
            # Send confirmation
            confirmation_msg = f"""
🎉 *Appointment Confirmed!*

💇 **Service:** {appointment.get('service', 'haircut')}

*Please secure your booking.*
            """
            telegram.send_message(chat_id, confirmation_msg)
            
            # Show payment options
            service_type = appointment.get('service', 'haircut')
            amount = 500
            
            payment_handler = self._get_payment_handler()
            payment_handler.show_payment_options(chat_id, service_type, amount)
            
            # Clear states
            (
                get_user_state, set_user_state, clear_user_state,
                get_appointment_data, set_appointment_data, clear_appointment_data,
                get_conversation_context, set_conversation_context
            ) = self._get_conversation_states()
            
            clear_user_state(chat_id)
            clear_appointment_data(chat_id)
            
        except Exception as e:
            logger.error(f"Error completing booking: {e}")