 # bot/services/whatsapp_service.py
import requests
import json
import logging
from django.conf import settings
from bot.services.telegram_service import BaseMessageService

logger = logging.getLogger(__name__)

class WhatsAppService(BaseMessageService):
    def __init__(self):
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        self.business_number = getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '')
        self.api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v18.0')
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.business_number}/messages"
        
        logger.info(f"📱 WhatsApp Service initialized for business number: {self.business_number}")
    
    async def process_incoming_message(self, data):
        """Process incoming WhatsApp message"""
        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            message_data = changes.get('value', {}).get('messages', [{}])[0]
            
            user_phone = message_data.get('from', '')
            message_text = message_data.get('text', {}).get('body', '')
            
            if not user_phone or not message_text:
                logger.info("ℹ️ WhatsApp message missing required data")
                return
            
            # Route to appropriate handler
            await self.route_message(user_phone, message_text)
            
        except Exception as e:
            logger.error(f"❌ Error processing WhatsApp message: {e}")
    
    async def route_message(self, user_phone, message_text):
        """Route message to existing handlers"""
        try:
            from bot.handlers.message_handler import MessageHandler
            
            # Convert WhatsApp message to platform-agnostic format
            user_data = {
                'platform': 'whatsapp',
                'user_id': user_phone,
                'platform_user_id': f"whatsapp_{user_phone}",
                'phone_number': user_phone
            }
            
            logger.info(f"🔄 Routing WhatsApp message from {user_phone}: {message_text}")
            
            handler = MessageHandler()
            # Check if handler has platform-agnostic method, fallback to existing method
            if hasattr(handler, 'handle_platform_message'):
                await handler.handle_platform_message(user_data, message_text)
            else:
                # Fallback: convert to Telegram-like format for existing handler
                telegram_like_update = {
                    'message': {
                        'chat': {'id': user_phone},
                        'text': message_text,
                        'from': {'id': user_phone}
                    }
                }
                handler.handle_update(telegram_like_update)
                
        except Exception as e:
            logger.error(f"❌ Error routing WhatsApp message: {e}")
    
    async def send_message(self, user_phone, message):
        """Send message via WhatsApp API"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": user_phone,
            "text": {"body": message}
        }
        
        try:
            logger.info(f"📤 Sending WhatsApp message to {user_phone}: {message[:50]}...")
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"✅ WhatsApp message sent successfully to {user_phone}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error sending WhatsApp message to {user_phone}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"📄 Response content: {e.response.text}")
            return False
    
    async def send_quick_reply(self, user_phone, message, options):
        """Send quick reply buttons"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        quick_replies = []
        for option in options[:3]:  # WhatsApp limits to 3 quick replies
            quick_replies.append({
                "type": "reply",
                "reply": {
                    "id": f"option_{option.replace(' ', '_').lower()}",
                    "title": option[:20]  # Limit title length
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": user_phone,
            "text": {"body": message},
            "quick_replies": quick_replies
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"✅ WhatsApp quick replies sent to {user_phone}")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp quick replies: {e}")
            return False
    
    async def send_template_message(self, user_phone, template_name, parameters=None):
        """Send WhatsApp template message"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        components = []
        if parameters:
            components = [{
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            }]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": user_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp template: {e}")
            return False

    def verify_webhook(self, verify_token, challenge):
        """Verify webhook endpoint"""
        expected_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        if verify_token == expected_token:
            return challenge
        return None