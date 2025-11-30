# bot/services/huggingface_service.py
import logging
import random
from django.conf import settings

logger = logging.getLogger(__name__)

# Check if AI dependencies are available
try:
    import requests
    AI_DEPENDENCIES_AVAILABLE = True
except ImportError:
    AI_DEPENDENCIES_AVAILABLE = False
    logger.warning("⚠️ AI dependencies not available - running in fallback mode")

class HuggingFaceService:
    def __init__(self):
        self.api_key = getattr(settings, 'HUGGINGFACE_API_KEY', '')
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
        
        # Check if we can actually use AI services
        self.ai_available = AI_DEPENDENCIES_AVAILABLE and bool(self.api_key)
        
        if not self.ai_available:
            logger.info("🤖 Running in fallback mode - AI services not available")
    
    def generate_enhanced_response(self, user_message, customer_context=None, salon_context=None):
        """Enhanced response generation with context - COMPATIBILITY METHOD"""
        logger.info(f"Enhanced response called - AI Available: {self.ai_available}")
        
        # If AI is not available, use intelligent fallback immediately
        if not self.ai_available:
            return self._get_intelligent_fallback(user_message)
        
        # For now, we'll ignore the context and use the existing response generation
        return self.generate_response(user_message)
        
    def generate_response(self, user_message, chat_history=None):
        """Generate response using Hugging Face model or fallback"""
        # If AI dependencies are missing, use fallback immediately
        if not self.ai_available:
            logger.info("🤖 Using fallback response (AI not available)")
            return self._get_intelligent_fallback(user_message)
        
        try:
            # If no API key, use fallback
            if not self.api_key:
                return self._get_intelligent_fallback(user_message)
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Create context-aware prompt
            prompt = self._create_kenyan_prompt(user_message)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 80,
                    "temperature": 0.8,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            logger.info(f"🤖 Sending request to Hugging Face API")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            # Handle different response scenarios
            if response.status_code == 503:
                logger.info("Model is loading, using fallback")
                return self._get_loading_response(user_message)
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, using fallback")
                return self._get_intelligent_fallback(user_message)
                
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '').strip()
                cleaned_response = self._clean_response(generated_text, user_message)
                logger.info(f"🤖 AI Response: {cleaned_response}")
                return cleaned_response
            else:
                logger.warning("Unexpected API response format")
                return self._get_intelligent_fallback(user_message)
                
        except requests.exceptions.Timeout:
            logger.error("Hugging Face API timeout")
            return self._get_intelligent_fallback(user_message)
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return self._get_intelligent_fallback(user_message)
    
    def _create_kenyan_prompt(self, user_message):
        """Create prompt with Kenyan salon context"""
        context = """Conversation with Frank, a Kenyan salon assistant at Frank Beauty Spot:
Frank is friendly, casual, uses some Swahili and Sheng naturally.
She helps with appointments, prices in KES, services, and M-Pesa payments.

User: hello
Frank: Mambo! Niaje? Karibu kwenye Frank Beauty Spot. Nisaidie na appointment, prices, au services?

User: how much for haircut?
Frank: Haircut iko between KES 500-1500, depending on style. Unapenda classic cut au something fancy?

User: book appointment
Frank: Poa! Sema tu date na time ungependa kuja. Tomorrow? Weekend? Morning au afternoon?

User: what services do you offer?
Frank: Tunatoa: haircut, hair color, treatment, manicure, pedicure, facials, makeup. Unavutiwa na nini?

User: can I pay with mpesa?
Frank: Yes! Tunakubali M-Pesa. Unaweza lipa deposit ya KES 500 kwa till 123456.

User: where are you ?
Frank: Tuko Tom Mboya Street, Nairobi CBD. Open Mon-Fri 8am-7pm. Karibu!

User: """
        
        return f"{context}{user_message}\nFrank:"
    
    def _clean_response(self, generated_text, user_message):
        """Clean the AI response"""
        # Remove user message if repeated
        cleaned = generated_text.replace(user_message, '').strip()
        
        # Extract only Frank's response
        if 'Frank:' in cleaned:
            cleaned = cleaned.split('Frank:')[-1].strip()
        
        # Remove any extra conversation artifacts
        if 'User:' in cleaned:
            cleaned = cleaned.split('User:')[0].strip()
        
        # Ensure we have a valid response
        if not cleaned or len(cleaned) < 3:
            return self._get_intelligent_fallback(user_message)
            
        return cleaned
    
    def _get_loading_response(self, user_message):
        """Response when model is loading"""
        loading_responses = [
            "Niko hapa! (Model iko loading kidogo...) Sema, unataka kujua bei, kubook appointment, au nini?",
            "Poa! (AI iko busy kidogo) Nisaidie na appointment, services, au prices zetu?",
            "Karibu! (System inafanya kazi...) Unataka kujua nini kuhusu salon services zetu?"
        ]
        return random.choice(loading_responses)
    
    def _get_intelligent_fallback(self, user_message):
        """Intelligent fallback based on user message"""
        message_lower = user_message.lower()
        
        greeting_words = ['hello', 'hi', 'hey', 'niaje', 'mambo', 'jambo','sasa']
        price_words = ['price', 'cost', 'how much', 'bei', 'pesa']
        booking_words = ['book', 'appointment', 'miadi', 'schedule', 'reserve']
        service_words = ['service', 'huduma', 'treatment', 'offer', 'do you have']
        payment_words = ['pay', 'payment', 'lipa', 'mpesa','tuma' ,'cash','nikuekee','weka','kwa hii number','kwa hii namba',"til"]
        location_words = ['where', 'location','located','address', 'tuko wapi', 'hapa']
        thank_words = ['thank', 'thanks', 'asante', 'shukran','wazi']
        
        if any(word in message_lower for word in greeting_words):
            return random.choice([
                "Mambo! Niaje? Karibu Frank Beauty Spot! 😊",
                "Hey! Poa? Niko hapa kukusort na salon services zetu.",
                "Hujambo! Karibu. Unataka kujua bei, kuweka appointment, au nini?"
            ])
        
        elif any(word in message_lower for word in price_words):
            return random.choice([
                "Bei zetu: Haircut KES 500-1500, Manicure KES 600-1200, Facial KES 1200-2500. Service gani unapenda?",
                "Prices: Haircut from KES 500, Manicure from KES 600, Facial from KES 1200. Affordable poa!",
                "Tuko reasonable! Haircut 500-1500, nails 600-1500, facials 1200-2500. Unavutiwa na service gani?"
            ])
        
        elif any(word in message_lower for word in booking_words):
            return random.choice([
                "Poa! Naweza kukusaidia kuweka appointment. Sema tu date na time ungependa kuja.",
                "Sawa! Tuweke appointment. Unaweza kuja lini? Tomorrow? Weekend? Sema tu preference yako.",
                "Perfect! Niku-bookie appointment. Preferred day na time? Morning, afternoon, weekend?"
            ])
        
        elif any(word in message_lower for word in service_words):
            return random.choice([
                "Tunafanya: Haircut & styling, Hair color, Treatment, Manicure, Pedicure, Facials, Makeup. Unataka kujua zaidi kuhusu gani?",
                "Services zetu: Everything hair, nails, facials, makeup! From basic cut to full glam. Service gani inakuvutia?",
                "Huduma zetu: Hair services, nail care, facial treatments, makeup. Sema tu unataka nini, nikusaidie!"
            ])
        
        elif any(word in message_lower for word in payment_words):
            return random.choice([
                "Tunakubali M-Pesa! Unaweza lipa deposit ya KES 500 kuhakikisha appointment, au pay full amount when you come.",
                "Lipa kwa M-Pesa! Till number: 123456. Unaweza lipa deposit au full amount. Flexible tu!",
                "M-Pesa iko poa! Lipa deposit ya KES 500 kwa till 123456, au cash when you visit. Your choice!"
            ])
        
        elif any(word in message_lower for word in location_words):
            return "Tuko Moi Avenue veteran house room 401, Nairobi CBD. Open Mon-Fri 8am-7pm, Sat 9am-6pm. Karibu!"
        
        elif any(word in message_lower for word in thank_words):
            return "Asante sana! Karibu tena. Kama una swali lingine, sema tu! 😊"
        
        else:
            return random.choice([
                "Asante kwa kuwasiliana! Nisaidie kidogo... Unataka kuweka appointment, kuuliza bei, au kujua services zetu?",
                "Pole, sijaelewa vizuri. Unaweza sema tena? Au unauliza kuhusu appointment, prices, au services?",
                "Niko hapa kukuhelp! Sema tu kama unataka appointment, prices, au kujua services zetu."
            ])
    
    def get_service_status(self):
        """Get the status of the AI service"""
        status_info = {
            'ai_dependencies_available': AI_DEPENDENCIES_AVAILABLE,
            'api_key_configured': bool(self.api_key),
            'service_available': self.ai_available,
            'mode': 'AI' if self.ai_available else 'Fallback'
        }
        
        if not AI_DEPENDENCIES_AVAILABLE:
            status_info['message'] = 'AI dependencies not installed - running in fallback mode'
        elif not self.api_key:
            status_info['message'] = 'HuggingFace API key not configured - running in fallback mode'
        else:
            status_info['message'] = 'AI service ready'
            
        return status_info