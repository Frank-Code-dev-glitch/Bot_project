# bot/views/whatsapp_views.py
import logging
import json
import asyncio
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

# Initialize message handler
try:
    from bot.handlers.message_handler import MessageHandler
    message_handler = MessageHandler()
    logger.info("✅ MessageHandler initialized successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import MessageHandler: {e}")
    message_handler = None
except Exception as e:
    logger.error(f"❌ Failed to initialize MessageHandler: {e}")
    message_handler = None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """Handle WhatsApp webhook requests"""
    
    if request.method == "GET":
        # Webhook verification
        hub_mode = request.GET.get("hub.mode")
        hub_verify_token = request.GET.get("hub.verify_token")
        hub_challenge = request.GET.get("hub.challenge")
        
        logger.info(f"🔐 Webhook verification request: mode={hub_mode}, challenge={hub_challenge}")
        
        try:
            from bot.services.whatsapp_service import WhatsAppService
            whatsapp_service = WhatsAppService()
            
            challenge_response = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
            
            if challenge_response:
                logger.info("✅ Webhook verification successful")
                return HttpResponse(challenge_response)
            else:
                logger.error("❌ Webhook verification failed")
                return HttpResponse("Verification failed", status=403)
                
        except ImportError as e:
            logger.error(f"❌ Failed to import WhatsAppService: {e}")
            return HttpResponse("Service unavailable", status=503)
        except Exception as e:
            logger.error(f"❌ Error during webhook verification: {e}")
            return HttpResponse("Server error during verification", status=500)
    
    elif request.method == "POST":
        try:
            # Parse the webhook data
            body = request.body.decode('utf-8')
            
            if not body:
                logger.warning("⚠️ Empty webhook payload received")
                return JsonResponse({"status": "ignored", "reason": "Empty payload"})
            
            webhook_data = json.loads(body)
            
            # Log the webhook data (safely, without sensitive info)
            safe_webhook_data = _sanitize_webhook_data(webhook_data)
            logger.info(f"📱 Received WhatsApp webhook: {json.dumps(safe_webhook_data, indent=2)}")
            
            if not message_handler:
                logger.error("❌ Message handler not available")
                return JsonResponse({"status": "error", "reason": "Handler unavailable"}, status=503)
            
            # Process the webhook data asynchronously
            try:
                # Use existing event loop or create new one
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async handler
                if loop.is_running():
                    # If loop is already running, create task
                    asyncio.create_task(message_handler.handle_whatsapp_webhook(webhook_data))
                    result = {"status": "queued", "message": "Processing in background"}
                else:
                    # Run in current loop
                    result = loop.run_until_complete(message_handler.handle_whatsapp_webhook(webhook_data))
                
                logger.info(f"✅ Webhook processed successfully: {result}")
                return JsonResponse(result)
                
            except Exception as async_error:
                logger.error(f"❌ Async processing error: {async_error}")
                return JsonResponse({"status": "error", "error": str(async_error)}, status=500)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in webhook: {e}")
            return JsonResponse({"status": "error", "error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"❌ Error processing WhatsApp webhook: {e}")
            return JsonResponse({"status": "error", "error": str(e)}, status=500)
    
    return HttpResponse("Method not allowed", status=405)

@csrf_exempt
@require_http_methods(["GET"])
def whatsapp_health_check(request):
    """Health check endpoint for WhatsApp service"""
    try:
        from bot.services.whatsapp_service import WhatsAppService
        whatsapp_service = WhatsAppService()
        
        # Basic service check
        status = {
            "status": "healthy",
            "service": "whatsapp",
            "phone_number_id": whatsapp_service.phone_number_id,
            "api_version": whatsapp_service.api_version,
            "message_handler": "available" if message_handler else "unavailable"
        }
        
        logger.info("✅ WhatsApp health check passed")
        return JsonResponse(status)
        
    except ImportError as e:
        logger.error(f"❌ Health check failed - import error: {e}")
        return JsonResponse({"status": "unhealthy", "error": "Service import failed"}, status=503)
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=503)

def _sanitize_webhook_data(webhook_data: dict) -> dict:
    """Remove sensitive information from webhook data for logging"""
    try:
        sanitized = json.loads(json.dumps(webhook_data))  # Create a copy
        
        # Remove message content for privacy
        if 'entry' in sanitized:
            for entry in sanitized['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if 'value' in change and 'messages' in change['value']:
                            for message in change['value']['messages']:
                                if 'text' in message:
                                    # Keep first few chars for context but redact most
                                    original_body = message['text'].get('body', '')
                                    if len(original_body) > 10:
                                        message['text']['body'] = original_body[:10] + '...***REDACTED***'
                                    else:
                                        message['text']['body'] = '***REDACTED***'
                                if 'from' in message:
                                    # Keep last 4 digits for identification
                                    phone = message['from']
                                    if len(phone) > 4:
                                        message['from'] = '***' + phone[-4:]
        
        return sanitized
    except Exception as e:
        logger.warning(f"⚠️ Could not sanitize webhook data: {e}")
        return {"error": "could_not_sanitize"}

# Class-based view alternative (if needed)
@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Class-based view for WhatsApp webhook"""
    
    def get(self, request, *args, **kwargs):
        """Handle webhook verification"""
        hub_mode = request.GET.get("hub.mode")
        hub_verify_token = request.GET.get("hub.verify_token")
        hub_challenge = request.GET.get("hub.challenge")
        
        logger.info(f"🔐 Webhook verification request (CBV): mode={hub_mode}")
        
        try:
            from bot.services.whatsapp_service import WhatsAppService
            whatsapp_service = WhatsAppService()
            
            challenge_response = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
            
            if challenge_response:
                logger.info("✅ Webhook verification successful (CBV)")
                return HttpResponse(challenge_response)
            else:
                logger.error("❌ Webhook verification failed (CBV)")
                return HttpResponse("Verification failed", status=403)
                
        except Exception as e:
            logger.error(f"❌ Error during webhook verification (CBV): {e}")
            return HttpResponse("Server error during verification", status=500)
    
    def post(self, request, *args, **kwargs):
        """Handle incoming messages"""
        try:
            body = request.body.decode('utf-8')
            
            if not body:
                logger.warning("⚠️ Empty webhook payload received (CBV)")
                return JsonResponse({"status": "ignored", "reason": "Empty payload"})
            
            webhook_data = json.loads(body)
            
            safe_webhook_data = _sanitize_webhook_data(webhook_data)
            logger.info(f"📱 Received WhatsApp webhook (CBV): {json.dumps(safe_webhook_data, indent=2)}")
            
            if not message_handler:
                logger.error("❌ Message handler not available (CBV)")
                return JsonResponse({"status": "error", "reason": "Handler unavailable"}, status=503)
            
            # Process asynchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(message_handler.handle_whatsapp_webhook(webhook_data))
                    result = {"status": "queued", "message": "Processing in background"}
                else:
                    result = loop.run_until_complete(message_handler.handle_whatsapp_webhook(webhook_data))
                
                logger.info(f"✅ Webhook processed successfully (CBV): {result}")
                return JsonResponse(result)
                
            except Exception as async_error:
                logger.error(f"❌ Async processing error (CBV): {async_error}")
                return JsonResponse({"status": "error", "error": str(async_error)}, status=500)
            
        except Exception as e:
            logger.error(f"❌ Error processing WhatsApp webhook (CBV): {e}")
            return JsonResponse({"status": "error", "error": str(e)}, status=500)