# bot/services/customer_memory.py
import logging
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CustomerMemory:
    def __init__(self, data_dir="data/customers"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info("CustomerMemory initialized")
    
    def _get_customer_file(self, chat_id):
        """Get the file path for a customer's data"""
        return os.path.join(self.data_dir, f"{chat_id}.json")
    
    def get_customer_data(self, chat_id):
        """Get customer data from file"""
        try:
            file_path = self._get_customer_file(chat_id)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error reading customer data: {e}")
            return {}
    
    def save_customer_data(self, chat_id, data):
        """Save customer data to file"""
        try:
            file_path = self._get_customer_file(chat_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving customer data: {e}")
    
    def remember_customer(self, chat_id):
        """Record or update customer interaction"""
        try:
            customer_data = self.get_customer_data(chat_id)
            
            # Initialize customer data if new
            if not customer_data:
                customer_data = {
                    'chat_id': chat_id,
                    'first_seen': datetime.now().isoformat(),
                    'interaction_count': 0,
                    'last_interaction': datetime.now().isoformat(),
                    'conversations': [],
                    'preferences': {
                        'preferred_services': [],
                        'payment_methods': []
                    }
                }
            
            # Update interaction data
            customer_data['interaction_count'] = customer_data.get('interaction_count', 0) + 1
            customer_data['last_interaction'] = datetime.now().isoformat()
            
            self.save_customer_data(chat_id, customer_data)
            logger.info(f"Remembered customer {chat_id}, interactions: {customer_data['interaction_count']}")
            
        except Exception as e:
            logger.error(f"Error remembering customer: {e}")
    
    def record_conversation(self, chat_id, user_message, bot_response):
        """Record a conversation exchange"""
        try:
            customer_data = self.get_customer_data(chat_id)
            
            if 'conversations' not in customer_data:
                customer_data['conversations'] = []
            
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_message': user_message,
                'bot_response': bot_response
            }
            
            customer_data['conversations'].append(conversation_entry)
            
            # Keep only last 50 conversations to prevent file bloat
            if len(customer_data['conversations']) > 50:
                customer_data['conversations'] = customer_data['conversations'][-50:]
            
            self.save_customer_data(chat_id, customer_data)
            
        except Exception as e:
            logger.error(f"Error recording conversation: {e}")
    
    def get_customer_context(self, chat_id):
        """Get customer context for AI responses"""
        try:
            customer_data = self.get_customer_data(chat_id)
            
            if not customer_data:
                return "New customer, first interaction."
            
            context_parts = []
            
            # Basic customer info
            interaction_count = customer_data.get('interaction_count', 0)
            context_parts.append(f"Customer has interacted {interaction_count} times.")
            
            # Preferred services
            preferred_services = customer_data.get('preferences', {}).get('preferred_services', [])
            if preferred_services:
                services_text = ", ".join(preferred_services)
                context_parts.append(f"Previously booked services: {services_text}")
            
            # Recent conversations (last 3)
            conversations = customer_data.get('conversations', [])
            if conversations:
                recent_convos = conversations[-3:]  # Last 3 conversations
                convo_context = "Recent conversations: "
                for convo in recent_convos:
                    convo_context += f"User said: '{convo.get('user_message', '')}', "
                context_parts.append(convo_context)
            
            return " ".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting customer context: {e}")
            return "Customer context unavailable."
    
    def get_personalized_greeting(self, chat_id):
        """Get personalized greeting based on customer history"""
        try:
            customer_data = self.get_customer_data(chat_id)
            
            if not customer_data or customer_data.get('interaction_count', 0) <= 1:
                return "Hello! 👋"
            
            interaction_count = customer_data.get('interaction_count', 0)
            preferred_services = customer_data.get('preferences', {}).get('preferred_services', [])
            
            if interaction_count > 5:
                if preferred_services:
                    service = preferred_services[0]
                    return f"Welcome back! 😊 Ready for another amazing {service}?"
                return "Great to see you again! 🎉"
            elif interaction_count > 2:
                return "Hello again! 👋 Good to see you back!"
            else:
                return "Welcome back! 😊"
                
        except Exception as e:
            logger.error(f"Error getting personalized greeting: {e}")
            return "Hello! 👋"
    
    def get_customer_preferences(self, chat_id):
        """Get customer preferences"""
        try:
            customer_data = self.get_customer_data(chat_id)
            return customer_data.get('preferences', {})
        except Exception as e:
            logger.error(f"Error getting customer preferences: {e}")
            return {}
    
    def record_service_preference(self, chat_id, service):
        """Record a service preference"""
        try:
            customer_data = self.get_customer_data(chat_id)
            preferences = customer_data.get('preferences', {})
            
            if 'preferred_services' not in preferences:
                preferences['preferred_services'] = []
            
            # Add service if not already in preferences
            if service not in preferences['preferred_services']:
                preferences['preferred_services'].append(service)
            
            # Keep only last 5 services to prevent bloat
            if len(preferences['preferred_services']) > 5:
                preferences['preferred_services'] = preferences['preferred_services'][-5:]
            
            customer_data['preferences'] = preferences
            self.save_customer_data(chat_id, customer_data)
            logger.info(f"Recorded service preference for {chat_id}: {service}")
            
        except Exception as e:
            logger.error(f"Error recording service preference: {e}")
    
    def record_payment_preference(self, chat_id, payment_method):
        """Record customer's preferred payment method"""
        try:
            customer_data = self.get_customer_data(chat_id)
            preferences = customer_data.get('preferences', {})
            
            if 'payment_methods' not in preferences:
                preferences['payment_methods'] = []
            
            if payment_method not in preferences['payment_methods']:
                preferences['payment_methods'].append(payment_method)
            
            customer_data['preferences'] = preferences
            self.save_customer_data(chat_id, customer_data)
            logger.info(f"Recorded payment preference for {chat_id}: {payment_method}")
            
        except Exception as e:
            logger.error(f"Error recording payment preference: {e}")