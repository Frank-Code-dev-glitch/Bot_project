# bot/views/telegram_views.py
import logging
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """Handle Telegram webhook requests"""
    try:
        # Parse the update
        body = request.body.decode('utf-8')
        update = json.loads(body)
        
        logger.info(f"📨 Received Telegram update: {update}")
        
        # Process the update
        from bot.handlers.message_handler import MessageHandler
        handler = MessageHandler()
        handler.handle_update(update)
        
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ Error processing Telegram webhook: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@require_http_methods(["GET"])
def set_telegram_webhook(request):
    """Set Telegram webhook URL"""
    try:
        from bot.services.telegram_service import TelegramService
        telegram = TelegramService()
        result = telegram.set_webhook()
        
        if result:
            return JsonResponse({"status": "success", "message": "Webhook set successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Failed to set webhook"}, status=500)
            
    except Exception as e:
        logger.error(f"❌ Error setting Telegram webhook: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@require_http_methods(["GET"])
def delete_telegram_webhook(request):
    """Delete Telegram webhook"""
    try:
        from bot.services.telegram_service import TelegramService
        telegram = TelegramService()
        result = telegram.delete_webhook()
        
        if result:
            return JsonResponse({"status": "success", "message": "Webhook deleted successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Failed to delete webhook"}, status=500)
            
    except Exception as e:
        logger.error(f"❌ Error deleting Telegram webhook: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        "status": "healthy", 
        "service": "frank-beauty-bot",
        "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime here
    })

@require_http_methods(["GET"]) 
def test_bot(request):
    """Test bot functionality"""
    try:
        from bot.services.telegram_service import TelegramService
        telegram = TelegramService()
        
        # Send a test message
        test_chat_id = "123456789"  # Replace with actual test chat ID
        message = "🤖 Bot is working! Test message from Frank Beauty Spot."
        
        success = telegram.send_message(test_chat_id, message)
        
        if success:
            return JsonResponse({"status": "success", "message": "Test message sent"})
        else:
            return JsonResponse({"status": "error", "message": "Failed to send test message"}, status=500)
            
    except Exception as e:
        logger.error(f"❌ Error testing bot: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa payment callbacks"""
    try:
        body = request.body.decode('utf-8')
        callback_data = json.loads(body)
        
        logger.info(f"💰 M-Pesa callback received: {callback_data}")
        
        # Process payment callback
        # Add your payment processing logic here
        
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
        
    except Exception as e:
        logger.error(f"❌ Error processing M-Pesa callback: {e}")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Failed"}, status=500)

@require_http_methods(["GET"])
def test_payment(request, phone_number, amount):
    """Test payment endpoint"""
    try:
        from bot.handlers.payment_handler import PaymentHandler
        payment_handler = PaymentHandler()
        
        result = payment_handler.initiate_mpesa_payment(
            phone_number, 
            amount, 
            "Test payment"
        )
        
        return JsonResponse({"status": "initiated", "result": result})
        
    except Exception as e:
        logger.error(f"❌ Error testing payment: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@require_http_methods(["GET"])
def payment_status(request):
    """Check payment status"""
    return JsonResponse({"status": "payment_status_endpoint"})

@require_http_methods(["GET"])
def service_info(request):
    """Get service information"""
    return JsonResponse({
        "services": ["hair", "nails", "facial", "makeup", "massage"],
        "prices": {"hair": "500-1500", "nails": "600-1200", "facial": "1200-2500"}
    })

@require_http_methods(["GET"])
def test_payment_flow(request):
    """Test complete payment flow"""