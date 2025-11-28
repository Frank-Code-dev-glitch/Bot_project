# bot/services/mpesa_service.py
import logging
import requests
import json
import base64
from datetime import datetime, timedelta
from bot.config.mpesa_config import MpesaConfig

logger = logging.getLogger(__name__)

class MpesaService:
    """M-Pesa service for handling payments via Daraja API"""
    
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.base_url = MpesaConfig.get_base_url()
        
        # Create session with better network handling
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.proxies.clear()
        
        logger.info(f"✅ MpesaService initialized - Environment: {MpesaConfig.get_environment()}")
    
    def _get_access_token(self):
        """Get M-Pesa OAuth access token"""
        try:
            # Check if token is still valid (55 minutes for safety)
            if (self.access_token and self.token_expiry and 
                datetime.now() < self.token_expiry):
                return self.access_token
            
            consumer_key = MpesaConfig.get_consumer_key()
            consumer_secret = MpesaConfig.get_consumer_secret()
            
            if not consumer_key or not consumer_secret:
                raise ValueError("M-Pesa consumer key or secret not configured")
            
            auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            logger.info("🔄 Requesting M-Pesa access token...")
            response = self.session.get(
                auth_url, 
                auth=(consumer_key, consumer_secret),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                # Token expires in 1 hour, set expiry to 55 minutes for safety
                self.token_expiry = datetime.now() + timedelta(minutes=55)
                logger.info("✅ M-Pesa access token obtained successfully")
                return self.access_token
            else:
                error_msg = f"Failed to get access token: {response.status_code}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            logger.error("❌ M-Pesa authentication timeout")
            raise Exception("M-Pesa servers are not responding")
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to M-Pesa servers")
            raise Exception("Check your internet connection")
        except Exception as e:
            logger.error(f"❌ Error getting M-Pesa token: {e}")
            raise
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate M-Pesa STK Push
        Returns: Dict with success/error information
        """
        try:
            # Validate configuration first
            MpesaConfig.validate_config()
            
            # Get access token
            access_token = self._get_access_token()
            
            # Generate password and timestamp
            password, timestamp = MpesaConfig.generate_password()
            
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return {
                    'success': False,
                    'error': "Invalid phone number format. Use 07XXXXXXXX or 2547XXXXXXXX"
                }
            
            # STK Push payload
            payload = {
                "BusinessShortCode": MpesaConfig.get_shortcode(),
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": formatted_phone,
                "PartyB": MpesaConfig.get_shortcode(),
                "PhoneNumber": formatted_phone,
                "CallBackURL": MpesaConfig.get_callback_url(),
                "AccountReference": account_reference[:12],
                "TransactionDesc": transaction_desc[:13]
            }
            
            logger.info(f"🔄 Initiating STK Push for {formatted_phone}, Amount: {amount}")
            
            # Make API request
            stk_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                stk_url, 
                json=payload, 
                headers=headers,
                timeout=20
            )
            
            logger.info(f"📡 STK Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_code = result.get('ResponseCode')
                
                if response_code == '0':
                    logger.info("✅ STK Push initiated successfully")
                    return {
                        'success': True,
                        'response_code': response_code,
                        'customer_message': result.get('CustomerMessage', 'Check your phone to complete payment'),
                        'checkout_request_id': result.get('CheckoutRequestID'),
                        'merchant_request_id': result.get('MerchantRequestID')
                    }
                else:
                    error_msg = result.get('errorMessage', 'STK Push failed')
                    logger.error(f"❌ STK Push API error: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'response_code': response_code
                    }
            else:
                error_msg = f"STK Push HTTP error: {response.status_code}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = "M-Pesa servers are not responding"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to M-Pesa servers"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            logger.error(f"❌ STK Push error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initiate_payment(self, phone_number, amount=1, service_name="Service"):
        """
        Simplified payment method for booking bot
        Returns: Dict with success/error information
        """
        try:
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return {
                    'success': False,
                    'error': f"Invalid phone number: {phone_number}"
                }
            
            # Use the main STK push method
            result = self.initiate_stk_push(
                phone_number=formatted_phone,
                amount=amount,
                account_reference=f"FRANK{service_name.upper().replace(' ', '')}",
                transaction_desc=f"Frank {service_name}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Payment initiation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_transaction_status(self, checkout_request_id):
        """
        Check status of an M-Pesa transaction
        """
        try:
            access_token = self._get_access_token()
            password, timestamp = MpesaConfig.generate_password()
            
            payload = {
                "BusinessShortCode": MpesaConfig.get_shortcode(),
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                query_url, 
                json=payload, 
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'result_code': result.get('ResultCode'),
                    'result_desc': result.get('ResultDesc')
                }
            else:
                return {
                    'success': False,
                    'error': f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Transaction status check error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_phone_number(self, phone_number):
        """
        Format phone number to 2547XXXXXXXX format
        """
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
        else:
            logger.warning(f"⚠️ Unrecognized phone format: {phone_number}")
            return None
    
    def validate_phone_number(self, phone_number):
        """Validate Kenyan phone number format"""
        formatted = self._format_phone_number(phone_number)
        return formatted is not None and formatted.startswith('2547') and len(formatted) == 12
    
    def get_service_status(self):
        """Check if M-Pesa service is properly configured and accessible"""
        try:
            MpesaConfig.validate_config()
            token = self._get_access_token()
            return {
                'status': 'active',
                'environment': MpesaConfig.get_environment(),
                'message': 'M-Pesa service is ready'
            }
        except Exception as e:
            return {
                'status': 'error',
                'environment': MpesaConfig.get_environment(),
                'message': str(e)
            }
    
    def test_connection(self):
        """Test M-Pesa API connectivity"""
        try:
            # Test basic internet
            test_response = requests.get("https://www.google.com", timeout=10)
            if test_response.status_code != 200:
                return {'success': False, 'error': 'No internet connection'}
            
            # Test M-Pesa service
            status = self.get_service_status()
            if status['status'] == 'active':
                return {'success': True, 'message': 'M-Pesa service is working'}
            else:
                return {'success': False, 'error': status['message']}
                
        except Exception as e:
            return {'success': False, 'error': f'Connection test failed: {str(e)}'}