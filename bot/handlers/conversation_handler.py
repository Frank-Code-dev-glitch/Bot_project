# bot/handlers/conversation_handler.py
import logging
from datetime import datetime, timedelta
from .conversation_states import (
    ConversationState,
    get_user_state, set_user_state,
    get_appointment_data, set_appointment_data,
    get_conversation_context, set_conversation_context,
    add_to_conversation_history,
    is_user_viewing_services, set_user_viewing_services,
    track_service_selection
)

logger = logging.getLogger(__name__)

class ConversationHandler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        
    def process_message(self, chat_id, text):
        """Main entry point for processing messages"""
        logger.info(f"Processing message from {chat_id}: {text}")
        
        # Add to conversation history
        add_to_conversation_history(chat_id, 'user', text)
        
        # Get current state
        current_state = get_user_state(chat_id)
        logger.info(f"Current state: {current_state}")
        
        # Handle based on state
        if current_state == ConversationState.IDLE:
            return self.handle_idle_state(chat_id, text)
        elif current_state == ConversationState.VIEWING_SERVICES:
            return self.handle_viewing_services(chat_id, text)
        elif current_state == ConversationState.AWAITING_SERVICE:
            return self.handle_awaiting_service(chat_id, text)
        elif current_state == ConversationState.AWAITING_DATE:
            return self.handle_awaiting_date(chat_id, text)
        elif current_state == ConversationState.AWAITING_TIME:
            return self.handle_awaiting_time(chat_id, text)
        elif current_state == ConversationState.AWAITING_NAME:
            return self.handle_awaiting_name(chat_id, text)
        elif current_state == ConversationState.AWAITING_PHONE:
            return self.handle_awaiting_phone(chat_id, text)
        elif current_state == ConversationState.AWAITING_CONFIRMATION:
            return self.handle_awaiting_confirmation(chat_id, text)
        else:
            # Default to idle state
            set_user_state(chat_id, ConversationState.IDLE)
            return self.handle_idle_state(chat_id, text)
    
    def handle_idle_state(self, chat_id, text):
        """Handle messages in idle state"""
        text_lower = text.lower()
        
        # Check for greetings
        if any(word in text_lower for word in ['hi', 'hello', 'hey', 'niaje', 'habari', 'start']):
            return self.bot.send_greeting(chat_id)
        
        # Check for service inquiry
        elif any(word in text_lower for word in ['service', 'services', 'offer', 'price', 'bei']):
            set_user_viewing_services(chat_id, True)
            return self.bot.send_services_list(chat_id)
        
        # Check for appointment with time
        elif self.is_appointment_with_time(text_lower):
            return self.start_appointment_with_time(chat_id, text)
        
        # Check for appointment request
        elif any(word in text_lower for word in ['book', 'appointment', 'schedule']):
            return self.start_appointment_flow(chat_id)
        
        # Check for location
        elif any(word in text_lower for word in ['where', 'location', 'address']):
            return self.bot.send_location_info(chat_id)
        
        # Check if this is a service selection
        elif self.is_service_selection(text_lower):
            service = self.extract_service(text_lower)
            return self.start_appointment_for_service(chat_id, service)
        
        # Default response
        else:
            return self.bot.send_main_menu(chat_id)
    
    def handle_viewing_services(self, chat_id, text):
        """Handle when user is viewing services"""
        text_lower = text.lower()
        
        # Check if user is selecting a service
        if self.is_service_selection(text_lower):
            service = self.extract_service(text_lower)
            track_service_selection(chat_id, service)
            return self.start_appointment_for_service(chat_id, service)
        
        # Check for appointment booking
        elif any(word in text_lower for word in ['book', 'appointment']):
            return self.start_appointment_flow(chat_id)
        
        # Otherwise, go back to idle
        else:
            set_user_state(chat_id, ConversationState.IDLE)
            return self.handle_idle_state(chat_id, text)
    
    def start_appointment_flow(self, chat_id):
        """Start appointment booking"""
        set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
        return self.bot.ask_for_service(chat_id)
    
    def start_appointment_for_service(self, chat_id, service):
        """Start booking for specific service"""
        # Save service to appointment data
        appointment = get_appointment_data(chat_id)
        appointment['service'] = service
        set_appointment_data(chat_id, appointment)
        
        # Move to next step
        set_user_state(chat_id, ConversationState.AWAITING_DATE)
        return self.bot.ask_for_date(chat_id, service)
    
    def start_appointment_with_time(self, chat_id, text):
        """Handle appointment request with time"""
        text_lower = text.lower()
        service = self.extract_service(text_lower)
        time_info = self.extract_time_info(text_lower)
        
        appointment = get_appointment_data(chat_id)
        
        if service:
            # User specified service and time
            appointment['service'] = service
            appointment['time_info'] = time_info
            appointment['time'] = self.parse_time(text_lower)
            appointment['date'] = self.parse_date(text_lower)
            
            set_appointment_data(chat_id, appointment)
            set_user_state(chat_id, ConversationState.AWAITING_NAME)
            return self.bot.ask_for_name_with_time(chat_id, service, time_info)
        else:
            # User only specified time, need service
            appointment['time_info'] = time_info
            set_appointment_data(chat_id, appointment)
            set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
            return self.bot.ask_for_service_with_time(chat_id, time_info)
    
    def handle_awaiting_service(self, chat_id, text):
        """Handle service selection"""
        text_lower = text.lower()
        
        if self.is_service_selection(text_lower):
            service = self.extract_service(text_lower)
            track_service_selection(chat_id, service)
            return self.start_appointment_for_service(chat_id, service)
        else:
            # Invalid service selection
            return self.bot.ask_for_service_again(chat_id)
    
    def handle_awaiting_date(self, chat_id, text):
        """Handle date selection"""
        date = self.parse_date(text.lower())
        if date:
            appointment = get_appointment_data(chat_id)
            appointment['date'] = date
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_TIME)
            return self.bot.ask_for_time(chat_id)
        else:
            return self.bot.ask_for_date_again(chat_id, appointment.get('service', ''))
    
    def handle_awaiting_time(self, chat_id, text):
        """Handle time selection"""
        time = self.parse_time(text.lower())
        if time:
            appointment = get_appointment_data(chat_id)
            appointment['time'] = time
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_NAME)
            return self.bot.ask_for_name(chat_id, appointment.get('service', ''))
        else:
            return self.bot.ask_for_time_again(chat_id)
    
    def handle_awaiting_name(self, chat_id, text):
        """Handle name input"""
        if len(text.strip()) > 1:
            appointment = get_appointment_data(chat_id)
            appointment['customer_name'] = text.strip()
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_PHONE)
            return self.bot.ask_for_phone(chat_id)
        else:
            return self.bot.ask_for_name_again(chat_id)
    
    def handle_awaiting_phone(self, chat_id, text):
        """Handle phone input"""
        if self.is_valid_phone(text):
            appointment = get_appointment_data(chat_id)
            appointment['customer_phone'] = text.strip()
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_CONFIRMATION)
            return self.bot.ask_for_confirmation(chat_id, appointment)
        else:
            return self.bot.ask_for_phone_again(chat_id)
    
    def handle_awaiting_confirmation(self, chat_id, text):
        """Handle confirmation"""
        text_lower = text.lower()
        
        if text_lower in ['yes', 'y', 'confirm', 'ok']:
            # Confirm appointment
            appointment = get_appointment_data(chat_id)
            success = self.bot.save_appointment(chat_id, appointment)
            
            if success:
                set_user_state(chat_id, ConversationState.AWAITING_PAYMENT)
                return self.bot.send_payment_options(chat_id, appointment)
            else:
                set_user_state(chat_id, ConversationState.IDLE)
                return self.bot.send_appointment_error(chat_id)
        
        elif text_lower in ['no', 'cancel']:
            set_user_state(chat_id, ConversationState.IDLE)
            return self.bot.send_appointment_cancelled(chat_id)
        
        else:
            # Ask again
            appointment = get_appointment_data(chat_id)
            return self.bot.ask_for_confirmation_again(chat_id, appointment)
    
    # Helper methods
    def is_appointment_with_time(self, text):
        text_lower = text.lower()
        time_words = ['tomorrow', 'today', 'morning', 'afternoon', 'evening', 'am', 'pm']
        appointment_words = ['book', 'appointment', 'schedule']
        
        has_time = any(word in text_lower for word in time_words)
        has_appointment = any(word in text_lower for word in appointment_words)
        
        return has_time and has_appointment
    
    def is_service_selection(self, text):
        service_keywords = ['hair', 'haircut', 'styling', 'manicure', 'pedicure', 
                          'facial', 'makeup', 'coloring', 'nails']
        return any(service in text for service in service_keywords)
    
    def extract_service(self, text):
        text_lower = text.lower()
        
        if 'hair' in text_lower or 'haircut' in text_lower:
            return 'Haircut & Styling'
        elif 'manicure' in text_lower or 'pedicure' in text_lower or 'nails' in text_lower:
            return 'Manicure/Pedicure'
        elif 'facial' in text_lower:
            return 'Facial Treatment'
        elif 'makeup' in text_lower:
            return 'Makeup Services'
        elif 'coloring' in text_lower:
            return 'Hair Coloring'
        return None
    
    def extract_time_info(self, text):
        text_lower = text.lower()
        
        if 'tomorrow' in text_lower and '2 pm' in text_lower:
            return "tomorrow at 2:00 PM"
        elif 'tomorrow' in text_lower:
            return "tomorrow"
        elif 'today' in text_lower:
            return "today"
        elif '2 pm' in text_lower:
            return "2:00 PM"
        return "soon"
    
    def parse_date(self, text):
        text_lower = text.lower()
        
        if 'tomorrow' in text_lower:
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        elif 'today' in text_lower:
            return datetime.now().strftime('%Y-%m-%d')
        return None
    
    def parse_time(self, text):
        text_lower = text.lower()
        
        if '2 pm' in text_lower or '2pm' in text_lower:
            return "14:00"
        elif '10 am' in text_lower:
            return "10:00"
        elif 'morning' in text_lower:
            return "09:00"
        elif 'afternoon' in text_lower:
            return "14:00"
        elif 'evening' in text_lower:
            return "17:00"
        return None
    
    def is_valid_phone(self, text):
        import re
        # Simple validation for Kenyan phone numbers
        pattern = r'^(\+?254|0)[17]\d{8}$'
        cleaned = re.sub(r'\D', '', text)
        return bool(re.match(pattern, cleaned))