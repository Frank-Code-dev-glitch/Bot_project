# bot/knowledge/salon_knowledge.py
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SalonKnowledge:
    def __init__(self):
        self.services = self._load_services()
        self.prices = self._load_prices()
        self.faqs = self._load_faqs()
        self.operating_hours = self._load_hours()
        self.staff = self._load_staff()
        self.knowledge_base = self._build_knowledge_base()
        logger.info("SalonKnowledge initialized with enhanced data")
    
    def _load_services(self):
        return {
            "hair_services": {
                "haircut": {
                    "name": "Haircut & Styling",
                    "description": "Professional haircut with styling and blow-dry",
                    "duration": "45-60 minutes",
                    "specialties": ["Classic Cut", "Layered Cut", "Bob Cut", "Pixie Cut"],
                    "keywords": ["haircut", "cut", "trim", "kukatwa", "style", "blow dry"]
                },
                "hair_color": {
                    "name": "Hair Coloring",
                    "description": "Full color, highlights, balayage, or root touch-up",
                    "duration": "2-3 hours",
                    "specialties": ["Highlights", "Balayage", "Full Color", "Root Touch-up"],
                    "keywords": ["color", "colour", "dye", "rangi", "highlight", "balayage"]
                },
                "treatment": {
                    "name": "Hair Treatment",
                    "description": "Deep conditioning and repair treatments",
                    "duration": "30-45 minutes",
                    "specialties": ["Keratin", "Protein", "Moisture", "Scalp Treatment"],
                    "keywords": ["treatment", "deep condition", "tiba", "keratin", "protein"]
                }
            },
            "beauty_services": {
                "manicure": {
                    "name": "Manicure",
                    "description": "Hand care, nail shaping, cuticle care, and polish",
                    "duration": "45-60 minutes",
                    "types": ["Basic", "Gel", "Acrylic", "Nail Art"],
                    "keywords": ["manicure", "nails", "kucha", "nail polish", "gel"]
                },
                "pedicure": {
                    "name": "Pedicure",
                    "description": "Foot care, callus removal, and nail care",
                    "duration": "45-60 minutes",
                    "types": ["Basic", "Spa", "Gel"],
                    "keywords": ["pedicure", "feet", "miguu", "foot care", "callus"]
                },
                "facial": {
                    "name": "Facial Treatment",
                    "description": "Customized facial based on skin type and concerns",
                    "duration": "60-75 minutes",
                    "types": ["Hydrating", "Anti-aging", "Acne Treatment", "Brightening"],
                    "keywords": ["facial", "face", "ufinyanzi", "uso", "skin", "glow"]
                },
                "makeup": {
                    "name": "Makeup Services",
                    "description": "Professional makeup application for events and special occasions",
                    "duration": "60-90 minutes",
                    "types": ["Natural", "Evening", "Bridal", "Editorial"],
                    "keywords": ["makeup", "make up", "beat", "foundation", "lipstick"]
                }
            }
        }
    
    def _load_prices(self):
        return {
            "haircut": {"range": "500-1500", "base": 800, "min": 500, "max": 1500},
            "hair_color": {"range": "1500-4000", "base": 2500, "min": 1500, "max": 4000},
            "treatment": {"range": "1000-2500", "base": 1500, "min": 1000, "max": 2500},
            "manicure": {"range": "600-1200", "base": 800, "min": 600, "max": 1200},
            "pedicure": {"range": "800-1500", "base": 1000, "min": 800, "max": 1500},
            "facial": {"range": "1200-2500", "base": 1800, "min": 1200, "max": 2500},
            "makeup": {"range": "1500-3000", "base": 2000, "min": 1500, "max": 3000}
        }
    
    def _load_faqs(self):
        return {
            "hours": {
                "question": "What are your operating hours?",
                "answer": "We're open Monday-Friday 8am-7pm, Saturday 9am-6pm, Sunday 10am-4pm"
            },
            "appointment": {
                "question": "How do I book an appointment?",
                "answer": "You can book through this bot, call us at 0712345678, or walk in during business hours"
            },
            "payment": {
                "question": "What payment methods do you accept?",
                "answer": "We accept M-Pesa (Till: 123456), cash, and debit/credit cards"
            },
            "cancellation": {
                "question": "What's your cancellation policy?",
                "answer": "You can cancel up to 2 hours before your appointment without charge"
            },
            "location": {
                "question": "Where are you located?",
                "answer": "Frank Beauty Spot, Tom Mboya Street, Nairobi CBD"
            },
            "parking": {
                "question": "Is there parking available?",
                "answer": "Yes, we have secure parking available for our customers"
            }
        }
    
    def _load_hours(self):
        return {
            "monday": {"open": "08:00", "close": "19:00"},
            "tuesday": {"open": "08:00", "close": "19:00"},
            "wednesday": {"open": "08:00", "close": "19:00"},
            "thursday": {"open": "08:00", "close": "19:00"},
            "friday": {"open": "08:00", "close": "19:00"},
            "saturday": {"open": "09:00", "close": "18:00"},
            "sunday": {"open": "10:00", "close": "16:00"}
        }
    
    def _load_staff(self):
        return {
            "stylists": [
                {"name": "Ann", "specialty": "Hair Coloring", "experience": "5 years"},
                {"name": "Grace", "specialty": "Haircuts", "experience": "3 years"},
                {"name": "Mike", "specialty": "Men's Grooming", "experience": "4 years"}
            ],
            "beauticians": [
                {"name": "Sarah", "specialty": "Facials", "experience": "4 years"},
                {"name": "Joy", "specialty": "Manicure & Pedicure", "experience": "2 years"}
            ],
            "reception": [
                {"name": "David", "role": "Receptionist"}
            ]
        }
    
    def _build_knowledge_base(self):
        """Build a comprehensive knowledge base for quick query matching"""
        knowledge = {}
        
        # Service descriptions
        for category_name, category in self.services.items():
            for service_key, service_info in category.items():
                knowledge[service_key] = service_info['description']
                for keyword in service_info.get('keywords', []):
                    knowledge[keyword] = service_info['description']
        
        # Price information
        for service, price_info in self.prices.items():
            knowledge[f"price {service}"] = f"KES {price_info['range']}"
            knowledge[f"cost {service}"] = f"KES {price_info['range']}"
        
        # FAQ answers
        for faq_key, faq_info in self.faqs.items():
            knowledge[faq_key] = faq_info['answer']
            # Add question variations as keys
            question_words = faq_info['question'].lower().split()
            for word in question_words:
                if len(word) > 3:  # Only significant words
                    knowledge[word] = faq_info['answer']
        
        # Operating hours
        knowledge["hours"] = self.faqs["hours"]["answer"]
        knowledge["open"] = self.faqs["hours"]["answer"]
        knowledge["close"] = self.faqs["hours"]["answer"]
        knowledge["operating"] = self.faqs["hours"]["answer"]
        
        # Location
        knowledge["location"] = self.faqs["location"]["answer"]
        knowledge["address"] = self.faqs["location"]["answer"]
        knowledge["where"] = self.faqs["location"]["answer"]
        
        return knowledge
    
    def get_context_for_query(self, user_message):
        """Get relevant salon knowledge for a user query"""
        try:
            user_message_lower = user_message.lower()
            relevant_info = []
            
            # Check service keywords
            for category_name, category in self.services.items():
                for service_key, service_info in category.items():
                    keywords = service_info.get('keywords', [])
                    if any(keyword in user_message_lower for keyword in keywords):
                        service_desc = f"{service_info['name']}: {service_info['description']} (Duration: {service_info['duration']})"
                        relevant_info.append(service_desc)
            
            # Check price queries
            if any(word in user_message_lower for word in ['price', 'cost', 'how much', 'pesa', 'bei']):
                price_context = "Our prices: "
                for service, price_info in self.prices.items():
                    price_context += f"{service.title()}: KES {price_info['range']}, "
                relevant_info.append(price_context)
            
            # Check operational queries
            if any(word in user_message_lower for word in ['open', 'close', 'hour', 'time', 'saa']):
                relevant_info.append(self.faqs["hours"]["answer"])
            
            if any(word in user_message_lower for word in ['location', 'address', 'where', 'place', 'wapi']):
                relevant_info.append(self.faqs["location"]["answer"])
            
            if any(word in user_message_lower for word in ['contact', 'call', 'phone', 'number', 'simu']):
                relevant_info.append("Call us at 0712345678 for immediate assistance")
            
            if any(word in user_message_lower for word in ['payment', 'pay', 'mpesa', 'cash', 'card', 'lipa']):
                relevant_info.append(self.faqs["payment"]["answer"])
            
            if any(word in user_message_lower for word in ['book', 'appointment', 'schedule', 'reserve']):
                relevant_info.append(self.faqs["appointment"]["answer"])
            
            if any(word in user_message_lower for word in ['cancel', 'cancellation']):
                relevant_info.append(self.faqs["cancellation"]["answer"])
            
            if any(word in user_message_lower for word in ['parking', 'park', 'garage']):
                relevant_info.append(self.faqs["parking"]["answer"])
            
            # If no specific info found, provide general salon info
            if not relevant_info:
                relevant_info.append("Frank Beauty Spot offers hair and beauty services including haircuts, coloring, treatments, manicures, pedicures, facials, and makeup.")
            
            return " ".join(relevant_info)
            
        except Exception as e:
            logger.error(f"Error getting context for query: {e}")
            return "Frank Beauty Spot - Your trusted beauty salon in Nairobi CBD."
    
    def get_service_details(self, service_name):
        """Get detailed information about a specific service"""
        for category in self.services.values():
            for service_key, service_info in category.items():
                if (service_name.lower() in service_key or 
                    service_name.lower() in service_info['name'].lower() or
                    any(service_name.lower() in keyword for keyword in service_info.get('keywords', []))):
                    return service_info
        return None
    
    def get_price_estimate(self, service_name, complexity="standard"):
        """Get price estimate based on service and complexity"""
        base_prices = {
            "standard": 1.0,
            "complex": 1.3,
            "premium": 1.6
        }
        
        # Find matching service
        for service_key, price_info in self.prices.items():
            if service_name.lower() in service_key:
                base_price = price_info["base"]
                multiplier = base_prices.get(complexity, 1.0)
                return int(base_price * multiplier)
        
        return None
    
    def is_open_now(self):
        """Check if salon is currently open"""
        try:
            now = datetime.now()
            current_day = now.strftime("%A").lower()
            current_time = now.strftime("%H:%M")
            
            if current_day in self.operating_hours:
                hours = self.operating_hours[current_day]
                return hours["open"] <= current_time <= hours["close"]
            return False
        except Exception as e:
            logger.error(f"Error checking opening hours: {e}")
            return True  # Default to open if there's an error
    
    def get_next_available_slot(self):
        """Get next available appointment slot"""
        try:
            now = datetime.now()
            
            if self.is_open_now():
                # If currently open, suggest within the next hour
                next_hour = (now + timedelta(hours=1)).strftime("%I:%M %p")
                return f"Today at {next_hour}"
            else:
                # If closed, suggest next opening
                current_day = now.strftime("%A").lower()
                days = list(self.operating_hours.keys())
                current_index = days.index(current_day) if current_day in days else -1
                
                if current_index >= 0:
                    # Find next open day
                    for i in range(1, 8):
                        next_day_index = (current_index + i) % 7
                        next_day = days[next_day_index]
                        if next_day in self.operating_hours:
                            open_time = self.operating_hours[next_day]["open"]
                            day_name = next_day.title()
                            return f"{day_name} at {open_time}"
                
                return "Tomorrow at 8:00 AM"
                
        except Exception as e:
            logger.error(f"Error getting next available slot: {e}")
            return "Tomorrow at 8:00 AM"
    
    def get_all_services(self):
        """Get all available services"""
        all_services = []
        for category in self.services.values():
            for service_info in category.values():
                all_services.append(service_info['name'])
        return all_services
    
    def get_service_by_keyword(self, keyword):
        """Find services matching a keyword"""
        matching_services = []
        keyword_lower = keyword.lower()
        
        for category in self.services.values():
            for service_key, service_info in category.items():
                if (keyword_lower in service_key or
                    keyword_lower in service_info['name'].lower() or
                    any(keyword_lower in kw for kw in service_info.get('keywords', []))):
                    matching_services.append(service_info)
        
        return matching_services
    
    def get_staff_by_specialty(self, specialty):
        """Get staff members by specialty"""
        matching_staff = []
        specialty_lower = specialty.lower()
        
        for role, staff_list in self.staff.items():
            for staff_member in staff_list:
                if (specialty_lower in staff_member.get('specialty', '').lower() or
                    specialty_lower in staff_member.get('role', '').lower() or
                    specialty_lower in staff_member['name'].lower()):
                    matching_staff.append(staff_member)
        
        return matching_staff