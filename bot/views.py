# bot/views.py
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from bot.handlers.message_handler import MessageHandler
from bot.handlers.payment_handler import PaymentHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def webhook(request):
    """
    Main webhook endpoint that receives updates from Telegram
    """
    try:
        # Parse the incoming update from Telegram
        update = json.loads(request.body.decode('utf-8'))
        logger.info(f"📱 Received Telegram update: {update}")
        
        # Process the update using our message handler
        handler = MessageHandler()
        handler.handle_update(update)
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_GET
def set_webhook_view(request):
    """
    View to manually set the webhook
    """
    try:
        from bot.services.telegram_service import TelegramService
        telegram_service = TelegramService()
        result = telegram_service.set_webhook()
        
        logger.info(f"🌐 Webhook set result: {result}")
        return JsonResponse({
            'status': 'success', 
            'message': 'Webhook configured successfully',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"❌ Set webhook error: {e}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to set webhook: {str(e)}'
        }, status=500)

@require_GET
def delete_webhook_view(request):
    """
    View to delete the webhook
    """
    try:
        from bot.services.telegram_service import TelegramService
        telegram_service = TelegramService()
        result = telegram_service.delete_webhook()
        
        logger.info(f"🌐 Webhook delete result: {result}")
        return JsonResponse({
            'status': 'success', 
            'message': 'Webhook deleted successfully',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"❌ Delete webhook error: {e}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to delete webhook: {str(e)}'
        }, status=500)

@require_GET
def health_check(request):
    """
    Comprehensive health check endpoint
    """
    try:
        health_status = {
            'status': 'healthy', 
            'service': 'Frank Beauty Salon Bot',
            'version': '2.0',
            'components': {}
        }
        
        # Test basic imports
        try:
            from bot.services.huggingface_service import HuggingFaceService
            ai = HuggingFaceService()
            test_response = ai.generate_response("Hello")
            health_status['components']['ai_service'] = 'operational'
            health_status['ai_test_response'] = test_response[:50] + '...' if len(test_response) > 50 else test_response
        except Exception as e:
            health_status['components']['ai_service'] = f'degraded: {str(e)}'
        
        # Test Telegram service
        try:
            from bot.services.telegram_service import TelegramService
            telegram = TelegramService()
            health_status['components']['telegram_service'] = 'operational'
            health_status['telegram_token_set'] = bool(telegram.token)
        except Exception as e:
            health_status['components']['telegram_service'] = f'degraded: {str(e)}'
        
        # Test Message Handler
        try:
            handler = MessageHandler()
            health_status['components']['message_handler'] = 'operational'
        except Exception as e:
            health_status['components']['message_handler'] = f'degraded: {str(e)}'
        
        # Test M-Pesa Service
        try:
            from bot.services.mpesa_service import MpesaService
            mpesa = MpesaService()
            token = mpesa.get_access_token()
            health_status['components']['mpesa_service'] = 'operational' if token else 'no_token'
            health_status['mpesa_token_available'] = bool(token)
        except Exception as e:
            health_status['components']['mpesa_service'] = f'degraded: {str(e)}'
        
        # Check if any critical components are degraded
        critical_components = ['telegram_service', 'message_handler']
        degraded_components = [comp for comp, status in health_status['components'].items() 
                             if 'degraded' in status and comp in critical_components]
        
        if degraded_components:
            health_status['status'] = 'degraded'
            health_status['degraded_components'] = degraded_components
        
        return JsonResponse(health_status)
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }, status=500)

@require_GET
def test_bot(request):
    """
    Comprehensive bot test endpoint
    """
    try:
        from bot.services.huggingface_service import HuggingFaceService
        from bot.services.telegram_service import TelegramService
        from bot.services.mpesa_service import MpesaService
        
        test_results = {
            'status': 'online',
            'service': 'Frank Beauty Salon Bot',
            'tests': {}
        }
        
        # Test AI Service
        try:
            ai = HuggingFaceService()
            test_response = ai.generate_response("Hello")
            test_results['tests']['ai_service'] = {
                'status': 'passed',
                'response_sample': test_response[:100] + '...' if len(test_response) > 100 else test_response
            }
        except Exception as e:
            test_results['tests']['ai_service'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test Telegram Service
        try:
            telegram = TelegramService()
            test_results['tests']['telegram_service'] = {
                'status': 'passed',
                'token_set': bool(telegram.token),
                'webhook_url': getattr(telegram, 'base_url', 'Not set')
            }
        except Exception as e:
            test_results['tests']['telegram_service'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test M-Pesa Service
        try:
            mpesa = MpesaService()
            token = mpesa.get_access_token()
            test_results['tests']['mpesa_service'] = {
                'status': 'passed' if token else 'partial',
                'access_token': bool(token),
                'demo_mode': True  # Assuming sandbox for testing
            }
        except Exception as e:
            test_results['tests']['mpesa_service'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Overall status
        failed_tests = [test for test, result in test_results['tests'].items() 
                       if result['status'] == 'failed']
        if failed_tests:
            test_results['status'] = 'degraded'
            test_results['failed_tests'] = failed_tests
        
        return JsonResponse(test_results)
        
    except Exception as e:
        logger.error(f"❌ Bot test error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Bot test failed: {str(e)}'
        }, status=500)

# bot/views.py - Update the mpesa_callback function
@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Handle M-Pesa payment callbacks with enhanced logging"""
    try:
        # Log raw request for debugging
        raw_body = request.body.decode('utf-8')
        logger.info(f"💰 M-Pesa callback received - Raw: {raw_body}")
        
        # Parse JSON data
        callback_data = json.loads(raw_body)
        logger.info(f"💰 M-Pesa callback parsed: {json.dumps(callback_data, indent=2)}")
        
        # Validate callback structure
        if not callback_data or 'Body' not in callback_data:
            logger.error("❌ Invalid M-Pesa callback structure")
            return JsonResponse({
                "ResultCode": 1, 
                "ResultDesc": "Invalid callback structure"
            })
        
        # Process callback with payment handler
        payment_handler = PaymentHandler()
        result = payment_handler.handle_payment_callback(callback_data)
        
        logger.info(f"💰 M-Pesa callback processing result: {result}")
        
        # Prepare response for M-Pesa API
        if result.get('status') in ['success', 'failed']:
            response_data = {
                "ResultCode": 0 if result.get('status') == 'success' else 1,
                "ResultDesc": result.get('message', 'Success' if result.get('status') == 'success' else 'Failed')
            }
            
            if result.get('booking_confirmed'):
                logger.info("✅ M-Pesa callback processed successfully - Appointment confirmed!")
            else:
                logger.warning(f"⚠️ M-Pesa payment processed but appointment not confirmed: {result.get('message')}")
        else:
            response_data = {
                "ResultCode": 1,
                "ResultDesc": result.get('message', 'Processing error')
            }
            logger.error(f"❌ M-Pesa callback processing error: {result.get('message')}")
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ M-Pesa callback JSON decode error: {e}")
        return JsonResponse({
            "ResultCode": 1, 
            "ResultDesc": "Invalid JSON format"
        })
        
    except Exception as e:
        logger.error(f"❌ M-Pesa callback processing error: {e}")
        return JsonResponse({
            "ResultCode": 1, 
            "ResultDesc": f"Server error: {str(e)}"
        })

@require_GET
def test_payment(request):
    """
    Enhanced test payment endpoint with parameters
    """
    try:
        # Get parameters from query string
        phone_number = request.GET.get('phone', '254712345678')
        amount = int(request.GET.get('amount', '1'))
        service_type = request.GET.get('service', 'haircut')
        
        from bot.services.mpesa_service import MpesaService
        mpesa = MpesaService()
        
        result = mpesa.initiate_stk_push(
            phone_number=phone_number, 
            amount=amount, 
            account_reference=f"TEST_{service_type}",
            description=f"Test {service_type}"
        )
        
        logger.info(f"🧪 Test payment initiated: {result}")
        
        response_data = {
            "status": "success",
            "message": "Test payment initiated",
            "test_data": {
                "phone_number": phone_number,
                "amount": amount,
                "service_type": service_type
            },
            "result": result
        }
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        logger.error(f"❌ Test payment parameter error: {e}")
        return JsonResponse({
            "status": "error", 
            "message": f"Invalid parameter: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"❌ Test payment error: {e}")
        return JsonResponse({
            "status": "error", 
            "message": f"Test payment failed: {str(e)}"
        }, status=500)

@require_GET
def payment_status(request):
    """
    Check payment status endpoint
    """
    try:
        checkout_request_id = request.GET.get('checkout_request_id')
        
        if not checkout_request_id:
            return JsonResponse({
                "status": "error",
                "message": "Missing checkout_request_id parameter"
            }, status=400)
        
        from bot.services.mpesa_service import MpesaService
        mpesa = MpesaService()
        
        status_result = mpesa.check_transaction_status(checkout_request_id)
        
        return JsonResponse({
            "status": "success",
            "checkout_request_id": checkout_request_id,
            "transaction_status": status_result
        })
        
    except Exception as e:
        logger.error(f"❌ Payment status check error: {e}")
        return JsonResponse({
            "status": "error",
            "message": f"Status check failed: {str(e)}"
        }, status=500)

@require_GET
def service_info(request):
    """
    Service information and configuration endpoint
    """
    config_info = {
        "service": "Frank Beauty Salon Bot",
        "version": "2.0",
        "features": [
            "Telegram Bot Integration",
            "AI-Powered Responses", 
            "M-Pesa Payment Processing",
            "Appointment Booking",
            "Customer Memory System"
        ],
        "endpoints": {
            "webhook": "/webhook/",
            "health_check": "/health/",
            "test_bot": "/test/",
            "mpesa_callback": "/mpesa_callback/",
            "test_payment": "/test_payment/",
            "payment_status": "/payment_status/",
            "set_webhook": "/set_webhook/",
            "delete_webhook": "/delete_webhook/"
        },
        "status": "operational"
    }
    
    # Add sensitive configuration info (masked)
    from django.conf import settings
    config_info['configuration'] = {
        'debug_mode': getattr(settings, 'DEBUG', False),
        'mpesa_configured': bool(getattr(settings, 'MPESA_CONSUMER_KEY', None)),
        'webhook_url_set': bool(getattr(settings, 'WEBHOOK_URL', None)),
        'ai_service': 'HuggingFace'
    }
    
    return JsonResponse(config_info)

# In views.py - add this endpoint for testing
@require_GET
def test_payment_flow(request):
    """Test payment flow directly"""
    try:
        chat_id = request.GET.get('chat_id', '123456789')
        service_type = request.GET.get('service', 'haircut')
        
        from bot.handlers.payment_handler import PaymentHandler
        payment = PaymentHandler()
        
        # Test showing payment options
        payment.show_payment_options(chat_id, service_type, 500)
        
        return JsonResponse({
            "status": "success",
            "message": f"Payment options sent to chat {chat_id} for {service_type}",
            "test": "Check your bot for payment buttons"
        })
        
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})