# bot/services/sentiment_analyzer.py
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def analyze_sentiment(self, text):
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'happy', 'thanks', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'angry', 'frustrated', 'disappointed']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative" 
        else:
            return "neutral"
    
    def get_appropriate_response(self, sentiment, message):
        """Get response based on sentiment"""
        if sentiment == "positive":
            return "That's great to hear! 😊 How can I help you today?"
        elif sentiment == "negative":
            return "I'm sorry to hear that. 😔 How can I make things better?"
        else:
            return None