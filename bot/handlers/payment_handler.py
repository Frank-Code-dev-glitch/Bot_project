# bot/handlers/payment_handler.py
import logging
import re
from bot.services.mpesa_service import MpesaService
from bot.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class PaymentHandler:
    def __init__(self):
        self.telegram = TelegramService()
        self.mpesa = MpesaService()
        logger.info("✅ PaymentHandler initialized with MpesaService")
    
    def show_payment_options(self, chat_id, service_type, amount):
        """Show payment options to user"""
        try:
            buttons = [
                [
                    {"text": "📱 M-Pesa STK Push", "callback_data": f"mpesa_stk_{service_type}_{amount}"},
                    {"text": "📋 Manual M-Pesa", "callback_data": f"mpesa_manual_{service_type}"}
                ],
                [
                    {"text": "💵 Pay Cash at Salon", "callback_data": f"cash_{service_type}"},
                    {"text": "🏠 Back to Menu", "callback_data": "back_to_menu"}
                ]
            ]
            
            payment_message = f"""
💳 *Secure Your Booking*

Please choose a payment method to confirm your appointment:

*Service:* {service_type.title()}
*Deposit:* KES {amount}

We accept M-Pesa and cash payments.
            """
            
            self.telegram.send_message_with_buttons(chat_id, payment_message, buttons)
            logger.info(f"✅ Payment options shown for {service_type}, amount: {amount}")
            
        except Exception as e:
            logger.error(f"❌ Error showing payment options: {e}")
            self.telegram.send_message(
                chat_id,
                "❌ Sorry, there was an error loading payment options. Please try again."
            )
    
    def initiate_mpesa_checkout(self, chat_id, service_type, amount):
        """Initiate M-Pesa STK Push flow"""
        try:
            message = f"""
📱 *M-Pesa STK Push*

Please reply with your M-Pesa registered phone number:

*Amount:* KES {amount}
*Service:* {service_type.title()}

📞 *Format:* 07XXXXXXXX or 2547XXXXXXXX

I'll send a payment request directly to your phone.
            """
            
            # Store payment context
            from bot.handlers.conversation_states import set_appointment_data
            set_appointment_data(chat_id, {
                'awaiting_phone': True,
                'service_type': service_type,
                'amount': amount,
                'payment_method': 'mpesa_stk'
            })
            
            self.telegram.send_message(chat_id, message)
            logger.info(f"🔄 Initiated M-Pesa checkout for {service_type}, amount: {amount}")
            
        except Exception as e:
            logger.error(f"❌ Error initiating M-Pesa checkout: {e}")
            self.telegram.send_message(
                chat_id,
                "❌ Sorry, there was an error starting payment. Please try again."
            )
    
    def process_phone_number(self, chat_id, phone_text, service_type, amount):
        """Process phone number for M-Pesa payment"""
        try:
            if not self._validate_phone_number(phone_text):
                self.telegram.send_message(
                    chat_id,
                    "❌ Invalid phone number format. Please use: *07XXXXXXXX* or *2547XXXXXXXX*"
                )
                return
            
            formatted_phone = self._format_phone_number(phone_text)
            
            # Send processing message
            self.telegram.send_message(
                chat_id,
                f"🔄 Initiating M-Pesa payment to {formatted_phone}..."
            )
            
            # Initiate STK Push
            result = self.mpesa.initiate_stk_push(
                phone_number=formatted_phone,
                amount=amount,
                account_reference=service_type.upper(),
                transaction_desc=f"{service_type} deposit"
            )
            
            if result['success']:
                success_message = f"""
✅ *M-Pesa Payment Initiated*

📱 Check your phone *{formatted_phone}* 
💳 Enter your M-Pesa PIN to complete payment

You'll receive a confirmation message from M-Pesa shortly.

*Once confirmed, your appointment will be secured!* 🎉
                """
                self.telegram.send_message(chat_id, success_message)
                logger.info(f"✅ STK Push initiated for {formatted_phone}")
                
                # Store transaction info for verification
                from bot.handlers.conversation_states import set_appointment_data
                set_appointment_data(chat_id, {
                    'checkout_request_id': result.get('checkout_request_id'),
                    'merchant_request_id': result.get('merchant_request_id'),
                    'payment_initiated': True
                })
                
            else:
                error_message = f"""
❌ *Payment Failed*

Sorry, we couldn't initiate the payment. 

*Error:* {result.get('error', 'Unknown error')}

Please try again or choose another payment method.
                """
                self.telegram.send_message(chat_id, error_message)
                logger.error(f"❌ STK Push failed: {result.get('error')}")
            
            # Clear the awaiting state
            from bot.handlers.conversation_states import set_appointment_data
            set_appointment_data(chat_id, {'awaiting_phone': False})
            
        except Exception as e:
            logger.error(f"❌ Error processing phone number: {e}")
            self.telegram.send_message(
                chat_id,
                "❌ Sorry, there was an error processing your payment. Please try again."
            )
            from bot.handlers.conversation_states import set_appointment_data
            set_appointment_data(chat_id, {'awaiting_phone': False})
    
    def show_manual_mpesa_instructions(self, chat_id, service_type):
        """Show manual M-Pesa payment instructions"""
        try:
            from bot.config.mpesa_config import MpesaConfig
            
            instructions = f"""
📋 *Manual M-Pesa Payment*

1. Go to *Lipa na M-Pesa*
2. Select *Pay Bill*
3. Business No: *{MpesaConfig.get_shortcode()}*
4. Account No: *{service_type.upper()}*
5. Amount: *KES 500*

6. Send and enter your M-Pesa PIN
7. Forward the confirmation message to me

We'll confirm your appointment once payment is received!
            """
            
            self.telegram.send_message(chat_id, instructions)
            logger.info(f"📋 Manual M-Pesa instructions shown for {service_type}")
            
        except Exception as e:
            logger.error(f"❌ Error showing manual instructions: {e}")
            self.telegram.send_message(
                chat_id,
                "❌ Error loading payment instructions. Please try STK Push instead."
            )
    
    def confirm_cash_payment(self, chat_id, service_type):
        """Confirm cash payment selection"""
        confirmation = f"""
💵 *Cash Payment Selected*

Great! We'll reserve your appointment for *{service_type}*.

Please bring *KES 500 deposit* when you visit.

📍 *Frank Beauty Spot*
Tom Mboya Street, Nairobi CBD

*We'll see you soon!* 😊

💡 *Pro tip:* You can pay now via M-Pesa to secure your slot instantly!
        """
        
        self.telegram.send_message(chat_id, confirmation)
        logger.info(f"💵 Cash payment confirmed for {service_type}")
    
    def _validate_phone_number(self, phone_number):
        """Validate Kenyan phone number format"""
        formatted = self._format_phone_number(phone_number)
        return formatted is not None
    
    def _format_phone_number(self, phone_number):
        """Format phone number to 2547XXXXXXXX format"""
        if not phone_number:
            return None
            
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(phone_number)))
        
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
            logger.warning(f"⚠️ Unrecognized phone format: {phone_number}")
            return None