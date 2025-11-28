# bot/config/mpesa_config.py
import os
import base64
from datetime import datetime
from django.conf import settings

class MpesaConfig:
    """M-Pesa configuration manager for Daraja API"""
    
    @staticmethod
    def get_consumer_key():
        return os.getenv('MPESA_CONSUMER_KEY', '')
    
    @staticmethod
    def get_consumer_secret():
        return os.getenv('MPESA_CONSUMER_SECRET', '')
    
    @staticmethod
    def get_shortcode():
        return os.getenv('MPESA_SHORTCODE', '174379')  # Sandbox default
    
    @staticmethod
    def get_passkey():
        return os.getenv('MPESA_PASSKEY', '')  # Get from Daraja portal
    
    @staticmethod
    def get_callback_url():
        return os.getenv('MPESA_CALLBACK_URL', 'https://yourdomain.com/mpesa/callback/')
    
    @staticmethod
    def get_environment():
        return os.getenv('MPESA_ENVIRONMENT', 'sandbox').lower()
    
    @staticmethod
    def is_production():
        return MpesaConfig.get_environment() == 'production'
    
    @staticmethod
    def get_base_url():
        """Get M-Pesa API base URL based on environment"""
        if MpesaConfig.is_production():
            return "https://api.safaricom.co.ke"
        else:
            return "https://sandbox.safaricom.co.ke"
    
    @staticmethod
    def generate_password():
        """Generate M-Pesa API password"""
        shortcode = MpesaConfig.get_shortcode()
        passkey = MpesaConfig.get_passkey()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if not shortcode or not passkey:
            raise ValueError("M-Pesa shortcode or passkey not configured")
        
        data_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(data_str.encode()).decode()
        return password, timestamp
    
    @staticmethod
    def validate_config():
        """Validate that all required M-Pesa credentials are set"""
        required_vars = [
            'MPESA_CONSUMER_KEY',
            'MPESA_CONSUMER_SECRET', 
            'MPESA_PASSKEY'
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing M-Pesa credentials: {', '.join(missing)}")
        
        return True
    
    @staticmethod
    def get_config_summary():
        """Get configuration summary for logging"""
        return {
            'environment': MpesaConfig.get_environment(),
            'base_url': MpesaConfig.get_base_url(),
            'shortcode': MpesaConfig.get_shortcode(),
            'consumer_key_set': bool(MpesaConfig.get_consumer_key()),
            'consumer_secret_set': bool(MpesaConfig.get_consumer_secret()),
            'passkey_set': bool(MpesaConfig.get_passkey())
        }