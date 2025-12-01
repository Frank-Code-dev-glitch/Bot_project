# bot/views/whatsapp_views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bot.handlers.whatsapp_conversation_handler import WhatsAppConversationHandler
from bot.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

# Initialize services
whatsapp_service = WhatsAppService()
conversation_handler = WhatsAppConversationHandler(whatsapp_service)

@csrf_exempt
def whatsapp_webhook(request):
    """Handle WhatsApp webhook"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"WhatsApp webhook received: {data}")
            
            # Extract message
            entries = data.get('entry', [])
            if not entries:
                return JsonResponse({"status": "no_entries"})
            
            changes = entries[0].get('changes', [])
            if not changes:
                return JsonResponse({"status": "no_changes"})
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if messages:
                message = messages[0]
                chat_id = message.get('from')
                text = message.get('text', {}).get('body', '').strip()
                
                if text:
                    # Process through conversation handler
                    conversation_handler.process_message(chat_id, text)
                    return JsonResponse({"status": "success"})
            
            return JsonResponse({"status": "no_message"})
            
        except Exception as e:
            logger.error(f"Error in WhatsApp webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    elif request.method == 'GET':
        # Verification
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verify_token = 'frank_beauty_token'  # Should be from settings
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("WhatsApp webhook verified")
            return JsonResponse({"hub.challenge": challenge})
        
        return JsonResponse({"error": "Verification failed"}, status=403)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)