# bot/services/whatsapp_service.py
import logging
import requests
import json
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        # Get credentials from environment variables with fallbacks
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '860715690464756')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'YOUR_VERIFY_TOKEN_HERE')
        self.api_version = "v24.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # Validate configuration
        if self.access_token == 'YOUR_ACCESS_TOKEN_HERE':
            logger.warning("⚠️ WhatsApp access token not configured. Set WHATSAPP_ACCESS_TOKEN environment variable.")
        
        logger.info(f"📱 WhatsApp Service initialized for phone number ID: {self.phone_number_id}")

    async def send_message(self, to_number: str, message_text: str) -> bool:
        """Send WhatsApp message using the Graph API"""
        try:
            # Ensure number format is correct
            formatted_number = self._format_phone_number(to_number)
            
            if not formatted_number:
                logger.error(f"❌ Invalid phone number format: {to_number}")
                return False
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"📤 Sending WhatsApp message to {formatted_number}: {message_text[:50]}...")
            logger.debug(f"🔧 Using URL: {url}")
            logger.debug(f"🔧 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ WhatsApp message sent successfully to {formatted_number}")
                logger.debug(f"📄 Response: {json.dumps(response_data, indent=2)}")
                return True
            else:
                logger.error(f"❌ Error sending WhatsApp message to {formatted_number}: {response.status_code} {response.reason}")
                
                # Detailed error logging
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                        error_details = {
                            'message': error_msg.get('message', 'Unknown error'),
                            'type': error_msg.get('type', 'Unknown'),
                            'code': error_msg.get('code', 'Unknown'),
                            'error_subcode': error_msg.get('error_subcode', 'None'),
                            'fbtrace_id': error_msg.get('fbtrace_id', 'None')
                        }
                        logger.error(f"🔍 Error details: {error_details}")
                        
                        # Specific handling for common errors
                        if error_msg.get('code') == 100:
                            logger.error("🔧 Possible solutions: Check Phone Number ID and Access Token")
                        elif error_msg.get('code') == 190:
                            logger.error("🔧 Possible solutions: Access Token expired or invalid")
                        elif error_msg.get('error_subcode') == 33:
                            logger.error("🔧 Possible solutions: Phone Number ID doesn't exist or permissions missing")
                            
                except Exception as parse_error:
                    logger.error(f"📄 Raw response content: {response.text}")
                    logger.error(f"🔍 Could not parse error response: {parse_error}")
                    
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout sending WhatsApp message to {to_number}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Connection error sending WhatsApp message to {to_number}")
            return False
        except Exception as e:
            logger.error(f"❌ Exception sending WhatsApp message to {to_number}: {str(e)}")
            return False

    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format phone number to international format (254XXXXXXXXX)"""
        try:
            # Remove any non-digit characters
            cleaned = ''.join(filter(str.isdigit, str(phone_number)))
            
            # Handle different formats
            if cleaned.startswith('0') and len(cleaned) == 10:
                # Convert 07... to 2547...
                return '254' + cleaned[1:]
            elif cleaned.startswith('7') and len(cleaned) == 9:
                # Convert 7... to 2547...
                return '254' + cleaned
            elif cleaned.startswith('254') and len(cleaned) == 12:
                # Already in correct format
                return cleaned
            elif cleaned.startswith('+254') and len(cleaned) == 13:
                # Convert +254... to 254...
                return cleaned[1:]
            else:
                logger.warning(f"⚠️ Unrecognized phone number format: {phone_number} (cleaned: {cleaned})")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error formatting phone number {phone_number}: {e}")
            return None

    async def send_quick_reply(self, to_number: str, message_text: str, quick_replies: List[str]) -> bool:
        """Send message with quick replies"""
        try:
            formatted_number = self._format_phone_number(to_number)
            if not formatted_number:
                return False
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Create quick reply buttons (max 3 allowed by WhatsApp)
            quick_reply_buttons = []
            for i, reply in enumerate(quick_replies[:3]):  # Limit to 3 buttons
                quick_reply_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": f"qr_{i+1}_{reply.lower().replace(' ', '_')}",
                        "title": reply
                    }
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message_text
                    },
                    "action": {
                        "buttons": quick_reply_buttons
                    }
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ WhatsApp quick reply sent to {formatted_number}")
                return True
            else:
                logger.error(f"❌ Error sending WhatsApp quick reply: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Exception sending WhatsApp quick reply: {e}")
            return False

    def verify_webhook(self, hub_mode: str, hub_verify_token: str, hub_challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook"""
        logger.info(f"🔐 Webhook verification attempt: mode={hub_mode}, token={hub_verify_token}")
        
        if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
            logger.info("✅ Webhook verified successfully")
            return hub_challenge
        else:
            logger.error(f"❌ Webhook verification failed. Expected token: {self.verify_token}, Got: {hub_verify_token}")
            return None

    def mark_message_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False

    async def send_template_message(self, to_number: str, template_name: str, parameters: List[Dict] = None) -> bool:
        """Send a template message"""
        try:
            formatted_number = self._format_phone_number(to_number)
            if not formatted_number:
                return False
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            template_data = {
                "name": template_name,
                "language": {"code": "en"}
            }
            
            if parameters:
                template_data["components"] = [{
                    "type": "body",
                    "parameters": parameters
                }]
            
            payload = {
                "messaging_product": "whatsapp",
                "to": formatted_number,
                "type": "template",
                "template": template_data
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            return False