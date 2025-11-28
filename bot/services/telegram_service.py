# bot/services/telegram_service.py
import os
import requests
import json
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, token=None):
        self.token = token or os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("Telegram bot token not found in environment variables")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session = self._create_session()
        logger.info("✅ TelegramService initialized")
    
    def _create_session(self):
        """Create requests session with proper configuration"""
        session = requests.Session()
        
        # Configure headers
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FrankBeautyBot/1.0'
        })
        
        # Configure proxy if available
        proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        if proxy_url:
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"🔧 Using proxy: {proxy_url}")
        
        return session
    
    def get_updates(self, offset=None, timeout=30, limit=100):
        """
        Get updates from Telegram using long polling
        """
        try:
            params = {
                'timeout': timeout,
                'limit': limit
            }
            
            if offset:
                params['offset'] = offset
            
            url = f"{self.base_url}/getUpdates"
            response = self.session.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('ok'):
                logger.error(f"Telegram API error: {data.get('description')}")
                return None
                
            return data
            
        except requests.exceptions.Timeout:
            logger.debug("Polling timeout - no new updates")
            return {'ok': True, 'result': []}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error getting updates: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting updates: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting updates: {e}")
            return None
    
    def send_message(self, chat_id, text, parse_mode='Markdown', reply_markup=None):
        """
        Send message to Telegram chat
        """
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = reply_markup
            
            url = f"{self.base_url}/sendMessage"
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ Message sent to {chat_id}")
                return result
            else:
                logger.error(f"❌ Failed to send message: {result.get('description')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error sending message: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error sending message: {e}")
            return None
    
    def send_message_with_buttons(self, chat_id, text, buttons, parse_mode='Markdown'):
        """
        Send message with inline keyboard buttons
        """
        try:
            keyboard = {
                'inline_keyboard': buttons
            }
            
            return self.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"❌ Error sending message with buttons: {e}")
            return None
    
    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """
        Answer callback query from inline buttons
        """
        try:
            payload = {
                'callback_query_id': callback_query_id
            }
            
            if text:
                payload['text'] = text
            if show_alert:
                payload['show_alert'] = show_alert
            
            url = f"{self.base_url}/answerCallbackQuery"
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Error answering callback query: {e}")
            return None
    
    def delete_message(self, chat_id, message_id):
        """
        Delete a message
        """
        try:
            payload = {
                'chat_id': chat_id,
                'message_id': message_id
            }
            
            url = f"{self.base_url}/deleteMessage"
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Error deleting message: {e}")
            return None
    
    def edit_message_text(self, chat_id, message_id, text, parse_mode='Markdown', reply_markup=None):
        """
        Edit existing message text
        """
        try:
            payload = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = reply_markup
            
            url = f"{self.base_url}/editMessageText"
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Error editing message: {e}")
            return None
    
    def set_webhook(self, webhook_url):
        """
        Set webhook for Telegram bot
        """
        try:
            payload = {
                'url': webhook_url,
                'drop_pending_updates': True
            }
            
            url = f"{self.base_url}/setWebhook"
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Webhook set: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error setting webhook: {e}")
            return None
    
    def delete_webhook(self):
        """
        Delete webhook
        """
        try:
            url = f"{self.base_url}/deleteWebhook"
            response = self.session.post(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info("✅ Webhook deleted")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error deleting webhook: {e}")
            return None
    
    def get_me(self):
        """
        Get bot information
        """
        try:
            url = f"{self.base_url}/getMe"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                logger.info(f"🤖 Bot info: {bot_info.get('first_name')} (@{bot_info.get('username')})")
                return bot_info
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting bot info: {e}")
            return None
    
    def test_connection(self):
        """
        Test connection to Telegram API
        """
        try:
            bot_info = self.get_me()
            if bot_info:
                return {
                    'status': 'connected',
                    'bot_name': bot_info.get('first_name'),
                    'bot_username': bot_info.get('username')
                }
            else:
                return {'status': 'failed', 'error': 'Could not get bot info'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}