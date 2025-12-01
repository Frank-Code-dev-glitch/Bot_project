# bot/handlers/whatsapp_conversation_handler.py
import logging
from datetime import datetime, timedelta
import re

from .conversation_states import (
    ConversationState,
    get_user_state, set_user_state,
    get_appointment_data, set_appointment_data,
    add_to_conversation_history, update_last_activity,
    is_user_viewing_services, set_user_viewing_services,
    track_service_selection,
    is_recently_viewed_services  # NEW IMPORT
)

logger = logging.getLogger(__name__)

class WhatsAppConversationHandler:
    """Handler specifically for WhatsApp conversations"""
    
    def __init__(self, whatsapp_service):
        self.whatsapp = whatsapp_service
    
    def process_message(self, chat_id, text):
        """Process WhatsApp message with conversation state"""
        try:
            logger.info(f"📱 Processing WhatsApp message from {chat_id}: {text}")
            
            # Update activity and history
            update_last_activity(chat_id)
            add_to_conversation_history(chat_id, 'user', text)
            
            # Get current state
            current_state = get_user_state(chat_id)
            logger.info(f"Current state for {chat_id}: {current_state}")
            
            # ========== THE FIX ==========
            # Check if user recently viewed services and is now selecting one
            if (current_state == ConversationState.IDLE and 
                is_recently_viewed_services(chat_id) and
                self._is_service_selection(text)):
                
                # User is selecting a service after seeing the list
                service = self._extract_service(text)
                if service:
                    logger.info(f"🎯 User selecting service after viewing services: {service}")
                    track_service_selection(chat_id, service)
                    return self.start_booking_for_service(chat_id, service)
            # ========== END FIX ==========
            
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
                # Default to idle
                set_user_state(chat_id, ConversationState.IDLE)
                return self.handle_idle_state(chat_id, text)
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            return self.send_error_message(chat_id)
    
    def handle_idle_state(self, chat_id, text):
        """Handle idle state messages"""
        text_lower = text.lower()
        
        # Greetings
        if any(word in text_lower for word in ['hi', 'hello', 'hey', 'niaje', 'habari', 'mambo', 'sasa']):
            return self.send_greeting(chat_id)
        
        # Services inquiry
        elif any(word in text_lower for word in ['service', 'services', 'offer', 'huduma', 'nini']):
            set_user_viewing_services(chat_id, True)
            return self.send_services_list(chat_id)
        
        # Location inquiry
        elif any(word in text_lower for word in ['where', 'location', 'wapi', 'address', 'place']):
            return self.send_location(chat_id)
        
        # Booking requests
        elif any(word in text_lower for word in ['book', 'appointment', 'weka', 'miadi', 'nikaweke']):
            return self.start_booking_flow(chat_id)
        
        # Booking with time
        elif self.is_booking_with_time(text_lower):
            return self.handle_booking_with_time(chat_id, text)
        
        # Service selection (might be direct)
        elif self._is_service_selection(text_lower):
            service = self._extract_service(text_lower)
            return self.start_booking_for_service(chat_id, service)
        
        # Default response
        else:
            return self.send_main_menu(chat_id)
    
    def handle_viewing_services(self, chat_id, text):
        """Handle when user just viewed services list"""
        text_lower = text.lower()
        
        # Check if user is selecting a service
        if self._is_service_selection(text_lower):
            service = self._extract_service(text_lower)
            track_service_selection(chat_id, service)
            return self.start_booking_for_service(chat_id, service)
        
        # Check for other actions
        elif any(word in text_lower for word in ['book', 'appointment', 'weka']):
            return self.start_booking_flow(chat_id)
        
        # If user asks something else, reset to idle
        else:
            set_user_state(chat_id, ConversationState.IDLE)
            return self.handle_idle_state(chat_id, text)
    
    def start_booking_flow(self, chat_id):
        """Start booking process"""
        set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
        return self.ask_for_service(chat_id)
    
    def start_booking_for_service(self, chat_id, service):
        """Start booking for specific service"""
        # Save service
        appointment = get_appointment_data(chat_id)
        appointment['service'] = service
        set_appointment_data(chat_id, appointment)
        
        # Move to next step
        set_user_state(chat_id, ConversationState.AWAITING_DATE)
        return self.ask_for_date(chat_id, service)
    
    def handle_booking_with_time(self, chat_id, text):
        """Handle booking request that includes time"""
        text_lower = text.lower()
        service = self._extract_service(text_lower)
        time_info = self.extract_time_info(text_lower)
        
        appointment = get_appointment_data(chat_id)
        
        if service:
            # User specified service and time
            appointment['service'] = service
            appointment['time_info'] = time_info
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_NAME)
            return self.ask_for_name_with_time(chat_id, service, time_info)
        else:
            # User only specified time, need service
            appointment['time_info'] = time_info
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_SERVICE)
            return self.ask_for_service_with_time(chat_id, time_info)
    
    def handle_awaiting_service(self, chat_id, text):
        """Handle service selection step"""
        text_lower = text.lower()
        
        if self._is_service_selection(text_lower):
            service = self._extract_service(text_lower)
            track_service_selection(chat_id, service)
            return self.start_booking_for_service(chat_id, service)
        else:
            return self.ask_for_service_again(chat_id)
    
    def handle_awaiting_date(self, chat_id, text):
        """Handle date selection step"""
        date = self.parse_date(text.lower())
        if date:
            appointment = get_appointment_data(chat_id)
            appointment['date'] = date
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_TIME)
            return self.ask_for_time(chat_id)
        else:
            appointment = get_appointment_data(chat_id)
            service = appointment.get('service', 'service')
            return self.ask_for_date_again(chat_id, service)
    
    def handle_awaiting_time(self, chat_id, text):
        """Handle time selection step"""
        time = self.parse_time(text.lower())
        if time:
            appointment = get_appointment_data(chat_id)
            appointment['time'] = time
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_NAME)
            return self.ask_for_name(chat_id, appointment.get('service', ''))
        else:
            return self.ask_for_time_again(chat_id)
    
    def handle_awaiting_name(self, chat_id, text):
        """Handle name input step"""
        if len(text.strip()) > 1:
            appointment = get_appointment_data(chat_id)
            appointment['customer_name'] = text.strip()
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_PHONE)
            return self.ask_for_phone(chat_id)
        else:
            return self.ask_for_name_again(chat_id)
    
    def handle_awaiting_phone(self, chat_id, text):
        """Handle phone input step"""
        if self.is_valid_phone(text):
            appointment = get_appointment_data(chat_id)
            appointment['customer_phone'] = text.strip()
            set_appointment_data(chat_id, appointment)
            
            set_user_state(chat_id, ConversationState.AWAITING_CONFIRMATION)
            return self.ask_for_confirmation(chat_id, appointment)
        else:
            return self.ask_for_phone_again(chat_id)
    
    def handle_awaiting_confirmation(self, chat_id, text):
        """Handle confirmation step"""
        text_lower = text.lower()
        
        if text_lower in ['yes', 'ndio', 'y', 'confirm', 'ok']:
            # Confirm appointment
            appointment = get_appointment_data(chat_id)
            
            # Save to database
            success = self.save_appointment(chat_id, appointment)
            
            if success:
                set_user_state(chat_id, ConversationState.AWAITING_PAYMENT)
                return self.send_payment_options(chat_id, appointment)
            else:
                set_user_state(chat_id, ConversationState.IDLE)
                return self.send_appointment_error(chat_id)
        
        elif text_lower in ['no', 'hapana', 'cancel', 'change']:
            # Cancel booking
            from .conversation_states import clear_user_state
            clear_user_state(chat_id)
            return self.send_appointment_cancelled(chat_id)
        
        else:
            # Ask again
            appointment = get_appointment_data(chat_id)
            return self.ask_for_confirmation_again(chat_id, appointment)
    
    # ========== HELPER METHODS ==========
    
    def _is_service_selection(self, text):
        """Check if text contains a service selection"""
        text_lower = text.lower()
        
        service_keywords = [
            'haircut', 'styling', 'hair', 'cut',
            'manicure', 'pedicure', 'nails',
            'facial', 'face', 'skin',
            'makeup', 'make up',
            'coloring', 'colour', 'color'
        ]
        
        return any(keyword in text_lower for keyword in service_keywords)
    
    def _extract_service(self, text):
        """Extract service name from text"""
        text_lower = text.lower()
        
        if 'hair' in text_lower or 'cut' in text_lower or 'styling' in text_lower:
            return 'Haircut & Styling'
        elif 'manicure' in text_lower or 'pedicure' in text_lower or 'nails' in text_lower:
            return 'Manicure/Pedicure'
        elif 'facial' in text_lower:
            return 'Facial Treatment'
        elif 'makeup' in text_lower:
            return 'Makeup Services'
        elif 'color' in text_lower or 'colour' in text_lower:
            return 'Hair Coloring'
        
        return None
    
    def is_booking_with_time(self, text):
        """Check if text contains booking with time"""
        time_words = ['tomorrow', 'today', 'morning', 'afternoon', 'evening', 'am', 'pm']
        booking_words = ['book', 'appointment', 'weka', 'miadi']
        
        has_time = any(word in text for word in time_words)
        has_booking = any(word in text for word in booking_words)
        
        return has_time and has_booking
    
    def extract_time_info(self, text):
        """Extract time information"""
        if 'tomorrow' in text and '2 pm' in text:
            return "tomorrow at 2:00 PM"
        elif 'tomorrow' in text:
            return "tomorrow"
        elif 'today' in text:
            return "today"
        elif '2 pm' in text:
            return "2:00 PM"
        return "soon"
    
    def parse_date(self, text):
        """Parse date from text"""
        if 'tomorrow' in text:
            tomorrow = datetime.now().date() + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        elif 'today' in text:
            return datetime.now().date().strftime('%Y-%m-%d')
        return None
    
    def parse_time(self, text):
        """Parse time from text"""
        if '2 pm' in text or '2pm' in text:
            return "14:00"
        elif 'morning' in text:
            return "09:00"
        elif 'afternoon' in text:
            return "14:00"
        elif 'evening' in text:
            return "17:00"
        return None
    
    def is_valid_phone(self, text):
        """Validate Kenyan phone number"""
        import re
        cleaned = re.sub(r'\D', '', text)
        return (len(cleaned) == 10 and cleaned.startswith('07')) or (len(cleaned) == 12 and cleaned.startswith('254'))
    
    # ========== RESPONSE METHODS ==========
    
    def send_greeting(self, chat_id):
        message = """Hello! Welcome to Frank Beauty Salon! 💇‍♀

How may I assist you today? 😊

You can:
• Ask about our services
• Book an appointment
• Check our prices
• Ask for our location"""
        return self.whatsapp.send_message(chat_id, message)
    
    def send_services_list(self, chat_id):
        message = """💇‍♀ *Our Services & Prices* 💅

• *Haircut & Styling* - From KES 500
• *Manicure/Pedicure* - From KES 600
• *Facial Treatment* - From KES 1,200
• *Makeup Services* - From KES 1,000
• *Hair Coloring* - From KES 1,500

*Which service interests you?* 😊

*Or would you like to book an appointment?*"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_service(self, chat_id):
        message = """Great! Let's book your appointment! 💅

*Which service would you like?*
• Haircut & Styling
• Manicure/Pedicure
• Facial Treatment
• Makeup Services
• Hair Coloring

*Please tell me the service you want.*"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_service_with_time(self, chat_id, time_info):
        message = f"""Perfect! You mentioned {time_info}. 💅

*Which service would you like for that time?*
• Haircut & Styling
• Manicure/Pedicure
• Facial Treatment
• Makeup Services
• Hair Coloring"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_date(self, chat_id, service):
        message = f"""Excellent choice! {service} it is! 📅

*When would you like to come in?*
• Today
• Tomorrow
• Specify a date (e.g., Monday, 15th Dec)"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_time(self, chat_id):
        message = """*What time works for you?* ⏰

• Morning (9 AM - 12 PM)
• Afternoon (2 PM - 5 PM)
• Evening (6 PM - 8 PM)
• Specific time (e.g., 2:30 PM)"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_name(self, chat_id, service):
        message = f"""Perfect! 😊

*Please tell me your name for the {service} appointment:*"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_name_with_time(self, chat_id, service, time_info):
        message = f"""Perfect! {service} on {time_info}. 😊

*Please tell me your name:*"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_phone(self, chat_id):
        message = """*Please provide your phone number:* 📱

Format: 07XXXXXXXX or 2547XXXXXXXX"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_confirmation(self, chat_id, appointment):
        summary = f"""📋 *APPOINTMENT SUMMARY* ✅

*Service:* {appointment.get('service', 'Not specified')}
*Date:* {appointment.get('date', 'Not specified')}
*Time:* {appointment.get('time', 'Not specified')}
*Name:* {appointment.get('customer_name', 'Not specified')}
*Phone:* {appointment.get('customer_phone', 'Not specified')}

---
*Is this information correct?*

Reply *YES* to confirm or *NO* to make changes."""
        return self.whatsapp.send_message(chat_id, summary)
    
    def send_location(self, chat_id):
        message = """📍 *Frank Beauty Spot*
Moi Avenue veteran house room 401, Nairobi CBD

*Hours:*
Mon-Fri: 8am - 7pm
Sat: 9am - 6pm  
Sun: 10am - 4pm

Come visit us! 🎉"""
        return self.whatsapp.send_message(chat_id, message)
    
    def send_main_menu(self, chat_id):
        message = """Hello! How can I assist you today? 😊

You can ask about:
• Our services
• Booking appointments
• Prices
• Location
• Or just say what you need! 💅"""
        return self.whatsapp.send_message(chat_id, message)
    
    # Retry/Error methods
    def ask_for_service_again(self, chat_id):
        message = """I didn't catch that. Which service would you like? 💅

• Haircut & Styling
• Manicure/Pedicure
• Facial Treatment
• Makeup Services
• Hair Coloring"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_date_again(self, chat_id, service):
        message = f"""For your {service}, when would you like to come? 📅

• Today
• Tomorrow
• Specific date"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_time_again(self, chat_id):
        message = """Please specify a time: ⏰

• Morning
• Afternoon
• Evening
• Specific time"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_name_again(self, chat_id):
        message = """Please provide your name:"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_phone_again(self, chat_id):
        message = """Please provide a valid Kenyan phone number:

Format: 07XXXXXXXX or 2547XXXXXXXX"""
        return self.whatsapp.send_message(chat_id, message)
    
    def ask_for_confirmation_again(self, chat_id, appointment):
        summary = f"""📋 *APPOINTMENT SUMMARY* 

*Service:* {appointment.get('service')}
*Date:* {appointment.get('date')}
*Time:* {appointment.get('time')}
*Name:* {appointment.get('customer_name')}
*Phone:* {appointment.get('customer_phone')}

Reply *YES* to confirm or *NO* to cancel."""
        return self.whatsapp.send_message(chat_id, summary)
    
    def send_error_message(self, chat_id):
        message = "Sorry, I encountered an error. Please try again! ❌"
        return self.whatsapp.send_message(chat_id, message)
    
    def send_appointment_error(self, chat_id):
        message = "Sorry, there was an error saving your appointment. Please try again! ❌"
        return self.whatsapp.send_message(chat_id, message)
    
    def send_appointment_cancelled(self, chat_id):
        message = "Appointment cancelled. You can book again anytime! 💅"
        return self.whatsapp.send_message(chat_id, message)
    
    def send_payment_options(self, chat_id, appointment):
        message = f"""💰 *PAYMENT OPTIONS* 💳

*Appointment:* {appointment.get('service')}

1. *M-Pesa Paybill:*
   - Paybill: 247247
   - Account: {chat_id[-6:]}

2. *Cash on arrival*

3. *Manual M-Pesa:*
   - Send to Till: 123456

*Please make payment to secure your booking!* ✅"""
        return self.whatsapp.send_message(chat_id, message)
    
    def save_appointment(self, chat_id, appointment):
        """Save appointment to database"""
        try:
            from bot.models import Appointment
            
            Appointment.objects.create(
                customer_whatsapp=chat_id,
                service_type=appointment.get('service', 'Haircut & Styling'),
                appointment_date=appointment.get('date', datetime.now().date()),
                appointment_time=appointment.get('time', '14:00'),
                customer_name=appointment.get('customer_name', 'Customer'),
                customer_phone=appointment.get('customer_phone', ''),
                status='pending',
                created_at=datetime.now()
            )
            
            logger.info(f"Appointment saved for {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
            return False