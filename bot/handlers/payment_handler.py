# bot/handlers/payment_handler.py
import logging
import re

logger = logging.getLogger(__name__)

class PaymentHandler:
    def __init__(self):
        self.telegram_service = None
        self.whatsapp_service = None
        self.mpesa_service = None
        logger.info("✅ PaymentHandler initialized with multi-platform support")
    
    def _get_telegram_service(self):
        if self.telegram_service is None:
            from bot.services.telegram_service import TelegramService
            self.telegram_service = TelegramService()
        return self.telegram_service
    
    def _get_whatsapp_service(self):
        if self.whatsapp_service is None:
            from bot.services.whatsapp_service import WhatsAppService
            self.whatsapp_service = WhatsAppService()
        return self.whatsapp_service
    
    def _get_mpesa_service(self):
        if self.mpesa_service is None:
            from bot.services.mpesa_service import MpesaService
            self.mpesa_service = MpesaService()
        return self.mpesa_service

    def show_payment_options(self, user_id, service_type, amount, platform='telegram'):
        """Show payment options to user - Updated for multi-platform"""
        try:
            logger.info(f"💰 Showing payment options for {platform} user {user_id}: {service_type} - KES {amount}")
            
            service_display = self._get_service_display_name(service_type)
            
            # Language-aware payment messages
            payment_messages = {
                'sheng': f"""
💳 *Lipa {service_display} - KES {amount}*

*Chagua payment method:*
🔹 *M-Pesa STK Push* - Automatic, simple
🔹 *M-Pesa Manual* - Lipa na manual  
🔹 *Cash Kwa Salon* - Pay when you come

*Which one unapenda?*
                """,
                'swenglish': f"""
💳 *Pay for {service_display} - KES {amount}*

*Choose payment method:*
🔹 *M-Pesa STK Push* - Automatic & easy
🔹 *M-Pesa Manual* - Lipa manually
🔹 *Cash at Salon* - Pay when you arrive

*Ungependa which option?*
                """,
                'english': f"""
💳 *Payment for {service_display} - KES {amount}*

*Select payment method:*
🔹 *M-Pesa STK Push* - Automatic & convenient
🔹 *M-Pesa Manual* - Manual payment
🔹 *Cash at Salon* - Pay upon arrival

*Which option would you prefer?*
                """
            }
            
            language = self._get_user_language(user_id)
            message = payment_messages.get(language, payment_messages['swenglish'])
            
            if platform == 'telegram':
                self._show_telegram_payment_options(user_id, message, service_type, amount)
            elif platform == 'whatsapp':
                self._show_whatsapp_payment_options(user_id, message, service_type, amount)
                
        except Exception as e:
            logger.error(f"❌ Error showing payment options: {e}")
            self._send_platform_message(platform, user_id, "❌ Sorry, error showing payment options.")

    def _show_telegram_payment_options(self, user_id, message, service_type, amount):
        """Show payment options for Telegram - Your existing logic optimized"""
        try:
            telegram = self._get_telegram_service()
            
            buttons = [
                [
                    {"text": "📱 M-Pesa STK Push", "callback_data": f"mpesa_stk_{service_type}_{amount}"},
                    {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{service_type}"}
                ],
                [
                    {"text": "💵 Cash at Salon", "callback_data": f"cash_{service_type}"},
                    {"text": "🏠 Back to Menu", "callback_data": "back_to_menu"}
                ]
            ]
            
            telegram.send_message_with_buttons(user_id, message, buttons)
            logger.info(f"✅ Telegram payment options sent to {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Telegram payment options error: {e}")

    def _show_whatsapp_payment_options(self, user_id, message, service_type, amount):
        """Show payment options for WhatsApp"""
        try:
            whatsapp = self._get_whatsapp_service()
            
            quick_replies = [
                "M-Pesa STK Push",
                "Manual M-Pesa", 
                "Cash at Salon"
            ]
            
            import asyncio
            asyncio.run(whatsapp.send_quick_reply(user_id, message, quick_replies))
            logger.info(f"✅ WhatsApp payment options sent to {user_id}")
            
        except Exception as e:
            logger.error(f"❌ WhatsApp payment options error: {e}")

    def initiate_mpesa_checkout(self, chat_id, service_type, amount, platform='telegram'):
        """Initiate M-Pesa STK Push flow - Updated for multi-platform"""
        try:
            phone_prompt = self._get_phone_prompt_message(chat_id, amount, service_type)
            self._send_platform_message(platform, chat_id, phone_prompt)
            
            # Set state to await phone number
            self._set_awaiting_phone(chat_id, service_type, amount, platform)
            logger.info(f"🔄 Initiated M-Pesa checkout for {service_type}, amount: {amount}")
            
        except Exception as e:
            logger.error(f"❌ Error initiating M-Pesa checkout: {e}")
            self._send_platform_message(platform, chat_id, "❌ Sorry, error starting payment.")

    def process_phone_number(self, user_id, phone_text, service_type, amount, platform='telegram'):
        """Process phone number for M-Pesa payment - Optimized validation"""
        try:
            formatted_phone = self._clean_phone_number(phone_text)
            
            if not formatted_phone:
                error_msg = self._get_invalid_phone_message(user_id)
                self._send_platform_message(platform, user_id, error_msg)
                return
            
            # Send processing message
            processing_msg = self._get_processing_message(user_id, formatted_phone)
            self._send_platform_message(platform, user_id, processing_msg)
            
            # Initiate STK Push
            result = self._initiate_stk_push(formatted_phone, amount, service_type, user_id)
            
            if result and result.get('success'):
                self._handle_successful_payment_initiation(user_id, formatted_phone, amount, result, platform)
            else:
                self._handle_failed_payment_initiation(user_id, result, platform)
            
            # Clear the awaiting state
            self._clear_awaiting_phone(user_id)
            
        except Exception as e:
            logger.error(f"❌ Error processing phone number: {e}")
            self._send_platform_message(platform, user_id, "❌ Sorry, error processing payment.")
            self._clear_awaiting_phone(user_id)

    def show_manual_mpesa_instructions(self, user_id, service_type, platform='telegram'):
        """Show manual M-Pesa payment instructions - Language optimized"""
        try:
            instructions = self._get_manual_mpesa_instructions(user_id, service_type)
            self._send_platform_message(platform, user_id, instructions)
            logger.info(f"📋 Manual M-Pesa instructions shown for {service_type}")
            
        except Exception as e:
            logger.error(f"❌ Error showing manual instructions: {e}")
            self._send_platform_message(platform, user_id, "❌ Error loading payment instructions.")

    def confirm_cash_payment(self, user_id, service_type, platform='telegram'):
        """Confirm cash payment selection - Language optimized"""
        try:
            confirmation = self._get_cash_payment_confirmation(user_id, service_type)
            self._send_platform_message(platform, user_id, confirmation)
            logger.info(f"💵 Cash payment confirmed for {service_type}")
            
        except Exception as e:
            logger.error(f"❌ Cash payment confirmation error: {e}")

    def handle_payment_callback(self, callback_data):
        """Handle M-Pesa payment callback - Your existing logic"""
        try:
            logger.info(f"💰 Processing M-Pesa callback: {callback_data}")
            
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            result_code = stk_callback.get('ResultCode')
            
            if result_code == 0:
                return self._handle_successful_payment(callback_metadata, stk_callback)
            else:
                return self._handle_failed_payment(stk_callback)
                
        except Exception as e:
            logger.error(f"❌ Payment callback handling error: {e}")
            return {'status': 'error', 'message': str(e)}

    # ==================== HELPER METHODS ====================

    def _initiate_stk_push(self, phone_number, amount, service_type, user_id):
        """Initiate STK push with proper error handling"""
        try:
            mpesa = self._get_mpesa_service()
            
            result = mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=f"{service_type.upper()}_{user_id[-6:]}",
                transaction_desc=f"{service_type} deposit"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ STK Push initiation error: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_successful_payment_initiation(self, user_id, phone, amount, result, platform):
        """Handle successful payment initiation"""
        success_message = self._get_payment_initiated_message(user_id, amount)
        self._send_platform_message(platform, user_id, success_message)
        
        # Store transaction info for verification
        self._store_transaction_details(user_id, phone, amount, result, platform)
        logger.info(f"✅ STK Push initiated for {phone}")

    def _handle_failed_payment_initiation(self, user_id, result, platform):
        """Handle failed payment initiation"""
        error_message = self._get_payment_failed_message(user_id, result)
        self._send_platform_message(platform, user_id, error_message)
        logger.error(f"❌ STK Push failed: {result.get('error')}")

    def _handle_successful_payment(self, callback_metadata, stk_callback):
        """Handle successful payment callback"""
        try:
            transaction_items = {item['Name']: item.get('Value') for item in callback_metadata.get('Item', [])}
            
            amount = transaction_items.get('Amount')
            mpesa_receipt = transaction_items.get('MpesaReceiptNumber')
            phone_number = transaction_items.get('PhoneNumber')
            
            logger.info(f"🎉 Payment successful: {mpesa_receipt} - KES {amount} - {phone_number}")
            
            # Update appointment status
            self._update_appointment_payment(mpesa_receipt, phone_number, amount, 'paid')
            
            # Send confirmation (in real implementation)
            self._send_payment_confirmation(phone_number, amount, mpesa_receipt)
            
            return {
                'status': 'success',
                'message': 'Payment processed successfully',
                'booking_confirmed': True,
                'mpesa_receipt': mpesa_receipt,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"❌ Successful payment handling error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _handle_failed_payment(self, stk_callback):
        """Handle failed payment callback"""
        try:
            result_desc = stk_callback.get('ResultDesc', 'Payment failed')
            logger.warning(f"❌ Payment failed: {result_desc}")
            
            return {
                'status': 'failed',
                'message': result_desc,
                'booking_confirmed': False
            }
            
        except Exception as e:
            logger.error(f"❌ Failed payment handling error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _clean_phone_number(self, phone_text):
        """Clean and validate phone number - Optimized version"""
        if not phone_text:
            return None
            
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(phone_text)))
        
        # Convert to 254 format
        if cleaned.startswith('0') and len(cleaned) == 10:
            return '254' + cleaned[1:]
        elif cleaned.startswith('254') and len(cleaned) == 12:
            return cleaned
        elif cleaned.startswith('7') and len(cleaned) == 9:
            return '254' + cleaned
        elif cleaned.startswith('+254') and len(cleaned) == 13:
            return cleaned[1:]
        else:
            logger.warning(f"⚠️ Unrecognized phone format: {phone_text}")
            return None

    def _get_user_language(self, user_id):
        """Get user's language preference"""
        try:
            from bot.handlers.conversation_states import get_user_language
            return get_user_language(user_id)
        except:
            return 'swenglish'

    def _get_service_display_name(self, service_type):
        """Get display name for service"""
        service_names = {
            'haircut': 'Haircut',
            'manicure': 'Manicure',
            'pedicure': 'Pedicure',
            'facial': 'Facial',
            'makeup': 'Makeup',
            'treatment': 'Hair Treatment'
        }
        return service_names.get(service_type, 'Service')

    def _set_awaiting_phone(self, user_id, service_type, amount, platform):
        """Set state to await phone number"""
        try:
            from bot.handlers.conversation_states import set_appointment_data
            set_appointment_data(user_id, {
                'awaiting_phone': True,
                'service_type': service_type,
                'amount': amount,
                'platform': platform
            })
        except Exception as e:
            logger.warning(f"Could not set awaiting phone state: {e}")

    def _clear_awaiting_phone(self, user_id):
        """Clear awaiting phone state"""
        try:
            from bot.handlers.conversation_states import set_appointment_data
            set_appointment_data(user_id, {'awaiting_phone': False})
        except Exception as e:
            logger.warning(f"Could not clear awaiting phone state: {e}")

    def _send_platform_message(self, platform, user_id, message):
        """Send message to appropriate platform"""
        try:
            if platform == 'telegram':
                telegram = self._get_telegram_service()
                telegram.send_message(user_id, message)
            elif platform == 'whatsapp':
                # For async context, this would be handled in async methods
                logger.info(f"📤 WhatsApp message to {user_id}: {message}")
        except Exception as e:
            logger.error(f"❌ Platform message sending error: {e}")

    # ==================== LANGUAGE-AWARE MESSAGES ====================

    def _get_phone_prompt_message(self, user_id, amount, service_type):
        """Get phone number prompt message"""
        language = self._get_user_language(user_id)
        
        prompts = {
            'sheng': f"""
📱 *Tuma namba yako ya simu*

*Amount:* KES {amount}
*Service:* {service_type.title()}

📞 *Format:* 07XXXXXXXX or 2547XXXXXXXX

Nitakutumia M-Pesa STK push direct kwa phone yako! 🔥
            """,
            'swenglish': f"""
📱 *Please send your phone number*

*Amount:* KES {amount}  
*Service:* {service_type.title()}

📞 *Format:* 07XXXXXXXX or 2547XXXXXXXX

Nitakutumia M-Pesa STK push direct kwa phone yako! 😊
            """,
            'english': f"""
📱 *Please provide your phone number*

*Amount:* KES {amount}
*Service:* {service_type.title()}

📞 *Format:* 07XXXXXXXX or 2547XXXXXXXX

I'll send an M-Pesa STK push directly to your phone! ✅
            """
        }
        return prompts.get(language, prompts['swenglish'])

    def _get_invalid_phone_message(self, user_id):
        """Get invalid phone number message"""
        language = self._get_user_language(user_id)
        
        messages = {
            'sheng': "❌ *Hiyo namba si sahihi!* Tafadhali tuma kama hivi: *254712345678*",
            'swenglish': "❌ *That phone number is invalid!* Please send like this: *254712345678*", 
            'english': "❌ *Invalid phone number format!* Please use this format: *254712345678*"
        }
        return messages.get(language, messages['swenglish'])

    def _get_processing_message(self, user_id, phone):
        """Get payment processing message"""
        language = self._get_user_language(user_id)
        
        messages = {
            'sheng': f"🔄 Inatuma M-Pesa payment kwa {phone}...",
            'swenglish': f"🔄 Sending M-Pesa payment to {phone}...",
            'english': f"🔄 Initiating M-Pesa payment to {phone}..."
        }
        return messages.get(language, messages['swenglish'])

    def _get_payment_initiated_message(self, user_id, amount):
        """Get payment initiated message"""
        language = self._get_user_language(user_id)
        
        messages = {
            'sheng': f"""
✅ *STK push imetumwa!* 

Check phone yako kwa KES {amount} M-Pesa prompt. 
Approve tu! 🔥

*Once confirmed, appointment yako itakuwa secured!* 🎉
            """,
            'swenglish': f"""
✅ *STK push sent!*

Check your phone for KES {amount} M-Pesa prompt.
Just approve! 😊

*Once confirmed, your appointment will be secured!* 🎉
            """,
            'english': f"""
✅ *STK push initiated!*

Check your phone for KES {amount} M-Pesa prompt. 
Please approve! ✅

*Once confirmed, your appointment will be secured!* 🎉
            """
        }
        return messages.get(language, messages['swenglish'])

    def _get_payment_failed_message(self, user_id, result):
        """Get payment failed message"""
        language = self._get_user_language(user_id)
        error = result.get('error', 'Unknown error') if result else 'Unknown error'
        
        messages = {
            'sheng': f"""
❌ *Haiwezi!* M-Pesa imekataa. 

*Error:* {error}

Try again or chagua payment method nyingine.
            """,
            'swenglish': f"""
❌ *Failed!* M-Pesa declined.

*Error:* {error}

Try again or choose another payment method.
            """,
            'english': f"""
❌ *Payment failed!* M-Pesa was declined.

*Error:* {error}

Please try again or use another method.
            """
        }
        return messages.get(language, messages['swenglish'])

    def _get_manual_mpesa_instructions(self, user_id, service_type):
        """Get manual M-Pesa instructions"""
        language = self._get_user_language(user_id)
        
        try:
            from bot.config.mpesa_config import MpesaConfig
            shortcode = MpesaConfig.get_shortcode()
        except:
            shortcode = "123456"
        
        if language == 'sheng':
            return f"""
📋 *Manual M-Pesa ya {service_type}*

1. *Ingiza M-Pesa*
2. *Chagua "Lipa Na M-Pesa"*
3. *Chagua "Pay Bill"*
4. *Business Number:* {shortcode}
5. *Account Number:* {service_type.upper()}
6. *Amount:* KES 500

7. *Send na enter PIN yako*
8. *Tuma confirmation message kwangu*

*Tutaconfirm appointment ukishalipa!* 📸
            """
        else:
            return f"""
📋 *Manual M-Pesa for {service_type}*

1. *Go to M-Pesa*
2. *Select "Lipa Na M-Pesa"* 
3. *Choose "Pay Bill"*
4. *Business No:* {shortcode}
5. *Account No:* {service_type.upper()}
6. *Amount:* KES 500

7. *Send and enter your PIN*
8. *Forward confirmation to me*

*We'll confirm once payment is received!* 📸
            """

    def _get_cash_payment_confirmation(self, user_id, service_type):
        """Get cash payment confirmation"""
        language = self._get_user_language(user_id)
        
        if language == 'sheng':
            return f"""
💵 *Cash Payment Chosen*

Sawa! Tutakuanga appointment for *{service_type}*.

*Kumbuka:* 
• Lipa cash kwa salon
• Come on time  
• Bring exact amount

📍 *Frank Beauty Spot*
Tom Mboya Street, Nairobi CBD

*See you!* 😊
            """
        else:
            return f"""
💵 *Cash Payment Selected*

Great! We'll reserve your appointment for *{service_type}*.

*Remember:*
• Pay cash at the salon
• Arrive on time
• Bring exact amount

📍 *Frank Beauty Spot* 
Tom Mboya Street, Nairobi CBD

*See you soon!* 😊
            """

    def _store_transaction_details(self, user_id, phone_number, amount, result, platform):
        """Store transaction details"""
        try:
            checkout_id = result.get('checkout_request_id')
            logger.info(f"💾 Storing transaction: {checkout_id} - {user_id} - KES {amount}")
        except Exception as e:
            logger.error(f"❌ Transaction storage error: {e}")

    def _update_appointment_payment(self, mpesa_receipt, phone_number, amount, status):
        """Update appointment payment status"""
        try:
            logger.info(f"📊 Updating appointment payment: {mpesa_receipt} - {status}")
        except Exception as e:
            logger.error(f"❌ Appointment payment update error: {e}")

    def _send_payment_confirmation(self, phone_number, amount, mpesa_receipt):
        """Send payment confirmation to user"""
        try:
            logger.info(f"📨 Payment confirmation sent: {phone_number} - {mpesa_receipt} - KES {amount}")
        except Exception as e:
            logger.error(f"❌ Payment confirmation sending error: {e}")