# bot/handlers/conversation_states.py
from enum import Enum

class ConversationState(Enum):
    IDLE = "idle"
    APPOINTMENT_IN_PROGRESS = "appointment_in_progress"
    AWAITING_DATE = "awaiting_date"
    AWAITING_TIME = "awaiting_time"
    AWAITING_SERVICE = "awaiting_service"
    AWAITING_CONFIRMATION = "awaiting_confirmation"

# Simple in-memory storage
user_states = {}
appointment_data = {}
conversation_context = {}  # Track what we've already asked

def get_user_state(chat_id):
    return user_states.get(chat_id, ConversationState.IDLE)

def set_user_state(chat_id, state):
    user_states[chat_id] = state

def clear_user_state(chat_id):
    user_states.pop(chat_id, None)
    appointment_data.pop(chat_id, None)
    conversation_context.pop(chat_id, None)

def get_appointment_data(chat_id):
    return appointment_data.get(chat_id, {})

def set_appointment_data(chat_id, data):
    if chat_id not in appointment_data:
        appointment_data[chat_id] = {}
    appointment_data[chat_id].update(data)

def get_conversation_context(chat_id):
    return conversation_context.get(chat_id, {})

def set_conversation_context(chat_id, context):
    if chat_id not in conversation_context:
        conversation_context[chat_id] = {}
    conversation_context[chat_id].update(context)

def clear_appointment_data(chat_id):
    appointment_data.pop(chat_id, None)
    conversation_context.pop(chat_id, None)
    
# bot/handlers/conversation_states.py - Add these functions
def get_payment_data(chat_id):
    """Get payment-specific data"""
    return get_appointment_data(chat_id).get('payment_data', {})

def set_payment_data(chat_id, payment_data):
    """Set payment-specific data"""
    appointment_data = get_appointment_data(chat_id) or {}
    appointment_data['payment_data'] = payment_data
    set_appointment_data(chat_id, appointment_data)

def clear_payment_data(chat_id):
    """Clear payment data"""
    appointment_data = get_appointment_data(chat_id) or {}
    if 'payment_data' in appointment_data:
        del appointment_data['payment_data']
    set_appointment_data(chat_id, appointment_data)