# bot/services/analytics.py
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self):
        self.analytics_file = "bot_analytics.json"
        self.data = self._load_data()
    
    def _load_data(self):
        try:
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"daily_stats": {}, "popular_services": {}}
    
    def record_interaction(self, interaction_type, details=None):
        """Record bot interactions"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.data["daily_stats"]:
            self.data["daily_stats"][today] = {
                "total_interactions": 0,
                "appointments_booked": 0,
                "payments_initiated": 0
            }
        
        self.data["daily_stats"][today]["total_interactions"] += 1
        
        if interaction_type == "appointment":
            self.data["daily_stats"][today]["appointments_booked"] += 1
        
        if interaction_type == "payment":
            self.data["daily_stats"][today]["payments_initiated"] += 1
        
        self._save_data()
    
    def get_daily_stats(self):
        """Get today's statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data["daily_stats"].get(today, {})