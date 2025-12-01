# bot/handlers/conversation_states.py
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    IDLE = "idle"
    APPOINTMENT_IN_PROGRESS = "appointment_in_progress"
    AWAITING_SERVICE_SELECTION = "awaiting_service_selection"
    AWAITING_DATE = "awaiting_date"
    AWAITING_TIME = "awaiting_time"
    AWAITING_SERVICE = "awaiting_service"
    AWAITING_NAME = "awaiting_name"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_COMPLETED = "payment_completed"
    CHOOSING_LANGUAGE = "choosing_language"
    VIEWING_SERVICES = "viewing_services"  # New state for when user is viewing services

# Simple in-memory storage with conversation tracking
user_states = {}
appointment_data = {}
conversation_context = {}  # Track conversation flow, last message, etc.
user_last_message = {}  # Track last bot message to user
conversation_history = {}  # Track conversation history

def get_user_state(chat_id):
    """Get current conversation state for user"""
    state = user_states.get(chat_id, ConversationState.IDLE)
    logger.debug(f"Getting state for {chat_id}: {state}")
    return state

def set_user_state(chat_id, state):
    """Set conversation state for user"""
    logger.debug(f"Setting state for {chat_id}: {state}")
    user_states[chat_id] = state
    
    # Update conversation context with state change
    ctx = get_conversation_context(chat_id)
    ctx['last_state_change'] = datetime.now().isoformat()
    ctx['current_state'] = state.value
    set_conversation_context(chat_id, ctx)

def clear_user_state(chat_id):
    """Clear all user states and data"""
    logger.debug(f"Clearing all states for {chat_id}")
    user_states.pop(chat_id, None)
    appointment_data.pop(chat_id, None)
    conversation_context.pop(chat_id, None)
    user_last_message.pop(chat_id, None)
    conversation_history.pop(chat_id, None)

def get_appointment_data(chat_id):
    """Get appointment data for user"""
    data = appointment_data.get(chat_id, {})
    logger.debug(f"Getting appointment data for {chat_id}: {data}")
    return data.copy()  # Return copy to prevent accidental mutation

def set_appointment_data(chat_id, data):
    """Set appointment data for user"""
    logger.debug(f"Setting appointment data for {chat_id}: {data}")
    if chat_id not in appointment_data:
        appointment_data[chat_id] = {}
    appointment_data[chat_id].update(data)
    
    # Also update conversation context
    ctx = get_conversation_context(chat_id)
    ctx['last_appointment_update'] = datetime.now().isoformat()
    set_conversation_context(chat_id, ctx)

def get_conversation_context(chat_id):
    """Get conversation context for user"""
    context = conversation_context.get(chat_id, {})
    logger.debug(f"Getting context for {chat_id}: {context}")
    return context.copy()

def set_conversation_context(chat_id, context):
    """Set conversation context for user"""
    logger.debug(f"Setting context for {chat_id}: {context}")
    if chat_id not in conversation_context:
        conversation_context[chat_id] = {}
    conversation_context[chat_id].update(context)

def clear_appointment_data(chat_id):
    """Clear appointment data but keep user state"""
    logger.debug(f"Clearing appointment data for {chat_id}")
    appointment_data.pop(chat_id, None)
    
    # Clear appointment-related context but keep other context
    ctx = get_conversation_context(chat_id)
    keys_to_remove = ['last_topic', 'last_service_mentioned', 'last_time_mentioned']
    for key in keys_to_remove:
        ctx.pop(key, None)
    set_conversation_context(chat_id, ctx)

def get_last_bot_message(chat_id):
    """Get last message sent by bot to user"""
    return user_last_message.get(chat_id, "")

def set_last_bot_message(chat_id, message):
    """Set last message sent by bot to user"""
    user_last_message[chat_id] = message

def add_to_conversation_history(chat_id, role, message):
    """Add message to conversation history"""
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    
    entry = {
        'role': role,  # 'user' or 'bot'
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    conversation_history[chat_id].append(entry)
    
    # Keep only last 10 messages to prevent memory issues
    if len(conversation_history[chat_id]) > 10:
        conversation_history[chat_id] = conversation_history[chat_id][-10:]

def get_conversation_history(chat_id, limit=5):
    """Get recent conversation history"""
    history = conversation_history.get(chat_id, [])
    return history[-limit:] if limit else history

def get_last_user_intent(chat_id):
    """Get the last detected intent from user messages"""
    history = get_conversation_history(chat_id, limit=3)
    for entry in reversed(history):
        if entry['role'] == 'user':
            message = entry['message'].lower()
            
            # Detect intents
            if any(word in message for word in ['book', 'appointment', 'schedule', 'weka', 'miadi']):
                return 'book_appointment'
            elif any(word in message for word in ['service', 'services', 'offer', 'price', 'bei', 'charge']):
                return 'ask_services'
            elif any(word in message for word in ['haircut', 'manicure', 'pedicure', 'facial', 'makeup', 'coloring']):
                return 'select_service'
            elif any(word in message for word in ['hi', 'hello', 'niaje', 'habari', 'hey']):
                return 'greeting'
            elif any(word in message for word in ['bye', 'goodbye', 'see you', 'asante']):
                return 'farewell'
    
    return None

def reset_to_idle_after_timeout(chat_id, timeout_minutes=30):
    """Reset user to idle state if conversation has timed out"""
    ctx = get_conversation_context(chat_id)
    last_activity = ctx.get('last_activity')
    
    if last_activity:
        last_activity_time = datetime.fromisoformat(last_activity)
        time_diff = (datetime.now() - last_activity_time).total_seconds() / 60
        
        if time_diff > timeout_minutes:
            logger.info(f"Resetting {chat_id} to idle due to {time_diff:.1f} minute timeout")
            clear_user_state(chat_id)
            return True
    
    return False

def update_last_activity(chat_id):
    """Update last activity timestamp"""
    ctx = get_conversation_context(chat_id)
    ctx['last_activity'] = datetime.now().isoformat()
    set_conversation_context(chat_id, ctx)

# Payment-related functions
def get_payment_data(chat_id):
    """Get payment-specific data"""
    data = get_appointment_data(chat_id)
    return data.get('payment_data', {})

def set_payment_data(chat_id, payment_data):
    """Set payment-specific data"""
    appointment = get_appointment_data(chat_id) or {}
    appointment['payment_data'] = payment_data
    set_appointment_data(chat_id, appointment)

def clear_payment_data(chat_id):
    """Clear payment data"""
    appointment = get_appointment_data(chat_id) or {}
    if 'payment_data' in appointment:
        del appointment['payment_data']
    set_appointment_data(chat_id, appointment)

def is_payment_pending(chat_id):
    """Check if payment is pending for user"""
    state = get_user_state(chat_id)
    return state == ConversationState.AWAITING_PAYMENT

def is_appointment_in_progress(chat_id):
    """Check if appointment booking is in progress"""
    state = get_user_state(chat_id)
    return state in [
        ConversationState.APPOINTMENT_IN_PROGRESS,
        ConversationState.AWAITING_SERVICE,
        ConversationState.AWAITING_DATE,
        ConversationState.AWAITING_TIME,
        ConversationState.AWAITING_NAME,
        ConversationState.AWAITING_PHONE,
        ConversationState.AWAITING_CONFIRMATION
    ]

def get_next_required_field(chat_id):
    """Get the next required field for appointment booking"""
    data = get_appointment_data(chat_id)
    
    if not data.get('service'):
        return 'service'
    elif not data.get('date'):
        return 'date'
    elif not data.get('time'):
        return 'time'
    elif not data.get('customer_name'):
        return 'name'
    elif not data.get('customer_phone'):
        return 'phone'
    else:
        return None

def get_incomplete_appointment_data(chat_id):
    """Get list of incomplete appointment fields"""
    data = get_appointment_data(chat_id)
    incomplete = []
    
    required_fields = ['service', 'date', 'time', 'customer_name', 'customer_phone']
    for field in required_fields:
        if not data.get(field):
            incomplete.append(field)
    
    return incomplete

def format_appointment_summary(chat_id):
    """Format appointment data as a summary string"""
    data = get_appointment_data(chat_id)
    
    summary_parts = []
    if data.get('service'):
        summary_parts.append(f"Service: {data['service']}")
    if data.get('date'):
        summary_parts.append(f"Date: {data['date']}")
    if data.get('time'):
        summary_parts.append(f"Time: {data['time']}")
    if data.get('customer_name'):
        summary_parts.append(f"Name: {data['customer_name']}")
    if data.get('customer_phone'):
        summary_parts.append(f"Phone: {data['customer_phone']}")
    
    return "\n".join(summary_parts) if summary_parts else "No appointment data yet"

# New helper functions for conversation flow
def is_user_viewing_services(chat_id):
    """Check if user recently viewed services"""
    ctx = get_conversation_context(chat_id)
    return ctx.get('last_topic') == 'services' or get_user_state(chat_id) == ConversationState.VIEWING_SERVICES

def set_user_viewing_services(chat_id, viewing=True):
    """Set user as viewing services"""
    if viewing:
        set_user_state(chat_id, ConversationState.VIEWING_SERVICES)
    set_conversation_context(chat_id, {'last_topic': 'services'})

def track_service_selection(chat_id, service):
    """Track that user selected a service"""
    ctx = get_conversation_context(chat_id)
    ctx['selected_service'] = service
    ctx['last_service_selection'] = datetime.now().isoformat()
    set_conversation_context(chat_id, ctx)

def get_last_selected_service(chat_id):
    """Get last selected service by user"""
    ctx = get_conversation_context(chat_id)
    return ctx.get('selected_service')

def _get_conversation_states():
    """Get all conversation state functions for easy access"""
    return (
        get_user_state, set_user_state, clear_user_state,
        get_appointment_data, set_appointment_data, clear_appointment_data,
        get_conversation_context, set_conversation_context,
        get_user_language, set_user_language
    )

# Language functions (if needed elsewhere)
def get_user_language(chat_id):
    """Get user's preferred language"""
    ctx = get_conversation_context(chat_id)
    return ctx.get('language', 'english')

def set_user_language(chat_id, language):
    """Set user's preferred language"""
    ctx = get_conversation_context(chat_id)
    ctx['language'] = language
    set_conversation_context(chat_id, ctx)

def cleanup_old_sessions(hours=24):
    """Clean up old conversation sessions to prevent memory leaks"""
    cutoff_time = datetime.now().timestamp() - (hours * 3600)
    
    # This is a simple implementation. In production, you'd want a more sophisticated approach
    logger.info(f"Cleaning up sessions older than {hours} hours")
    
    # Note: This is simplistic. In production, track session creation time
    pass