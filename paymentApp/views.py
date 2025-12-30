# payments/views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import HttpResponse
from django.views import View
from constance import config
import json
import razorpay

from subscriptionApp.models import SubscriptionPlansModel, SubscriptionDetails
from .models import Payment
from .serializers import (
    CreateSubscriptionOrderSerializer,
    PaymentSerializer,
    PaymentVerificationSerializer,
    AppleIAPVerificationSerializer
)
from .services.razorpay_service import razorpay_service
from .services.apple_iap_service import apple_iap_service


# ============================================================================
# RAZORPAY VIEWS
# ============================================================================

class CreateSubscriptionOrderAPIView(APIView):
    """
    Create Razorpay order for subscription purchase
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateSubscriptionOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan_id = serializer.validated_data['plan_id']
        
        try:
            # Get the subscription plan
            plan = SubscriptionPlansModel.objects.get(id=plan_id, is_active=True)
            
            # Check if user already has active subscription
            try:
                existing_subscription = SubscriptionDetails.objects.get(user=request.user)
                existing_subscription.check_and_update_status()
                
                if existing_subscription.is_active:
                    return Response({
                        'error': 'You already have an active subscription',
                        'expires_at': existing_subscription.expires_at,
                        'days_remaining': existing_subscription.days_remaining
                    }, status=status.HTTP_400_BAD_REQUEST)
            except SubscriptionDetails.DoesNotExist:
                pass
            
            # Get amount in paise
            amount = plan.get_amount_in_paise()
            
            # Create plan snapshot
            plan_snapshot = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'amount': float(plan.amount),
                'duration': plan.duration,
                'purchased_at': timezone.now().isoformat()
            }
            
            # Create Razorpay order
            razorpay_order = razorpay_service.create_order(
                amount=amount,
                currency='INR',
                notes={
                    'user_id': request.user.id,
                    'plan_id': plan.id,
                    'plan_name': plan.name
                }
            )
            
            # Create or get subscription record (inactive)
            subscription, created = SubscriptionDetails.objects.get_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'plan_snapshot': plan_snapshot,
                    'is_active': False
                }
            )
            
            if not created:
                # Update existing inactive subscription
                subscription.plan = plan
                subscription.plan_snapshot = plan_snapshot
                subscription.is_active = False
                subscription.save()
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                subscription=subscription,
                plan=plan,
                payment_provider='razorpay',
                razorpay_order_id=razorpay_order['id'],
                amount=amount,
                currency='INR',
                status='Created'
            )
            
            # Return response for Flutter - using constance config
            return Response({
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': 'INR',
                'key': config.RAZORPAY_KEY_ID,
                'payment_id': payment.id,
                'name': config.BUSINESS_NAME,
                'description': f'{plan.name} Subscription - {plan.duration} days',
                'prefill': {
                    'email': request.user.email,
                    'contact': getattr(request.user, 'phone', ''),
                    'name': request.user.get_full_name() or request.user.username
                },
                'theme': {
                    'color': config.RAZORPAY_THEME_COLOR
                },
                'plan_details': {
                    'name': plan.name,
                    'duration': plan.duration,
                    'amount': float(plan.amount)
                }
            }, status=status.HTTP_201_CREATED)
            
        except SubscriptionPlansModel.DoesNotExist:
            return Response({
                'error': 'Plan not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifySubscriptionPaymentAPIView(APIView):
    """
    Verify Razorpay payment and activate subscription
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        razorpay_order_id = serializer.validated_data['razorpay_order_id']
        razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
        razorpay_signature = serializer.validated_data['razorpay_signature']
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            # Verify payment signature
            razorpay_service.verify_signature(params_dict)
            
            # Get payment record
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                user=request.user
            )
            
            # Capture payment
            razorpay_service.capture_payment(razorpay_payment_id, payment.amount)
            
            # Update payment record
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'Success'
            payment.save()
            
            # Activate subscription
            subscription = payment.subscription
            if subscription:
                subscription.activate_subscription()
                
                from subscriptionApp.serializers import SubscriptionDetailsSerializer
                return Response({
                    'status': 'success',
                    'message': 'Subscription activated successfully',
                    'payment': PaymentSerializer(payment).data,
                    'subscription': SubscriptionDetailsSerializer(subscription).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Subscription record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except razorpay.errors.SignatureVerificationError:
            # Mark payment as failed
            Payment.objects.filter(
                razorpay_order_id=razorpay_order_id,
                user=request.user
            ).update(status='Failed')
            
            return Response({
                'status': 'failure',
                'message': 'Payment signature verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Payment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Payment record not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshPaymentStatusAPIView(APIView):
    """
    Check payment status with Razorpay and update subscription if payment succeeded
    Useful for stuck/pending transactions
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response({
                'error': 'order_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get payment record from database
            payment = Payment.objects.get(
                razorpay_order_id=order_id,
                user=request.user
            )
            
            # Check if already successful
            if payment.status == 'Success' and payment.subscription and payment.subscription.is_active:
                from subscriptionApp.serializers import SubscriptionDetailsSerializer
                return Response({
                    'status': 'already_active',
                    'message': 'Subscription is already active',
                    'payment': PaymentSerializer(payment).data,
                    'subscription': SubscriptionDetailsSerializer(payment.subscription).data
                }, status=status.HTTP_200_OK)
            
            # Fetch order details from Razorpay
            order = razorpay_service.client.order.fetch(order_id)
            
            # Fetch all payments for this order from Razorpay
            payments_list = razorpay_service.client.order.payments(order_id)
            
            if not payments_list or 'items' not in payments_list or len(payments_list['items']) == 0:
                return Response({
                    'status': 'no_payment',
                    'message': 'No payment attempted yet for this order',
                    'order_status': order.get('status'),
                    'amount_paid': order.get('amount_paid', 0),
                    'amount_due': order.get('amount_due', 0)
                }, status=status.HTTP_200_OK)
            
            # Get the latest payment
            razorpay_payment = payments_list['items'][0]
            payment_status = razorpay_payment.get('status')
            payment_id = razorpay_payment.get('id')
            
            # Update our database with latest info
            payment.razorpay_payment_id = payment_id
            payment.payment_method = razorpay_payment.get('method')
            
            if payment_status == 'captured':
                # Payment was successful - activate subscription
                payment.status = 'Success'
                payment.save()
                
                if payment.subscription and not payment.subscription.is_active:
                    payment.subscription.activate_subscription()
                
                from subscriptionApp.serializers import SubscriptionDetailsSerializer
                return Response({
                    'status': 'success',
                    'message': 'Payment verified and subscription activated',
                    'payment': PaymentSerializer(payment).data,
                    'subscription': SubscriptionDetailsSerializer(payment.subscription).data
                }, status=status.HTTP_200_OK)
                
            elif payment_status == 'authorized':
                # Payment authorized but not captured - capture it
                try:
                    razorpay_service.capture_payment(payment_id, payment.amount)
                    payment.status = 'Success'
                    payment.save()
                    
                    if payment.subscription and not payment.subscription.is_active:
                        payment.subscription.activate_subscription()
                    
                    from subscriptionApp.serializers import SubscriptionDetailsSerializer
                    return Response({
                        'status': 'success',
                        'message': 'Payment captured and subscription activated',
                        'payment': PaymentSerializer(payment).data,
                        'subscription': SubscriptionDetailsSerializer(payment.subscription).data
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({
                        'status': 'error',
                        'message': f'Failed to capture payment: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            elif payment_status == 'failed':
                payment.status = 'Failed'
                payment.error_code = razorpay_payment.get('error_code')
                payment.error_description = razorpay_payment.get('error_description')
                payment.save()
                
                return Response({
                    'status': 'failed',
                    'message': 'Payment has failed',
                    'error_code': payment.error_code,
                    'error_description': payment.error_description,
                    'payment': PaymentSerializer(payment).data
                }, status=status.HTTP_200_OK)
                
            else:
                # Payment is still pending/processing
                payment.status = payment_status.capitalize()
                payment.save()
                
                return Response({
                    'status': 'pending',
                    'message': f'Payment is still {payment_status}',
                    'payment_status': payment_status,
                    'payment': PaymentSerializer(payment).data
                }, status=status.HTTP_200_OK)
                
        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment record not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckOrderStatusAPIView(APIView):
    """
    Quick check of order status without full reconciliation
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            # Get payment from database
            payment = Payment.objects.get(
                razorpay_order_id=order_id,
                user=request.user
            )
            
            # Fetch from Razorpay
            order = razorpay_service.client.order.fetch(order_id)
            
            return Response({
                'order_id': order_id,
                'order_status': order.get('status'),
                'amount': order.get('amount'),
                'amount_paid': order.get('amount_paid', 0),
                'amount_due': order.get('amount_due', 0),
                'attempts': order.get('attempts', 0),
                'local_payment_status': payment.status,
                'subscription_active': payment.subscription.is_active if payment.subscription else False
            }, status=status.HTTP_200_OK)
            
        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionWebhookAPIView(APIView):
    """
    Handle Razorpay webhook events for subscriptions
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = config.RAZORPAY_WEBHOOK_SECRET
        webhook_body = request.body.decode('utf-8')
        
        if not webhook_signature:
            return Response(
                {'error': 'No signature provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            razorpay_service.verify_webhook_signature(
                webhook_body,
                webhook_signature,
                webhook_secret
            )
        except razorpay.errors.SignatureVerificationError:
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event_id = request.headers.get('X-Razorpay-Event-Id')
        webhook_data = json.loads(webhook_body)
        
        event = webhook_data.get('event')
        payload = webhook_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        
        if event == 'payment.captured':
            self.handle_payment_captured(payment_entity, event_id)
        elif event == 'payment.failed':
            self.handle_payment_failed(payment_entity, event_id)
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
    
    def handle_payment_captured(self, payment_entity, event_id):
        """Handle successful payment and activate subscription"""
        payment_id = payment_entity.get('id')
        order_id = payment_entity.get('order_id')
        
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
            
            if payment.webhook_event_id == event_id:
                return  # Skip duplicate
            
            payment.razorpay_payment_id = payment_id
            payment.status = 'Success'
            payment.webhook_event_id = event_id
            payment.save()
            
            # Activate subscription
            if payment.subscription and not payment.subscription.is_active:
                payment.subscription.activate_subscription()
            
        except Payment.DoesNotExist:
            pass
    
    def handle_payment_failed(self, payment_entity, event_id):
        """Handle failed payment"""
        order_id = payment_entity.get('order_id')
        
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
            
            if payment.webhook_event_id == event_id:
                return
            
            payment.status = 'Failed'
            payment.webhook_event_id = event_id
            payment.save()
            
        except Payment.DoesNotExist:
            pass


# ============================================================================
# APPLE IN-APP PURCHASE VIEWS
# ============================================================================

class VerifyAppleIAPAPIView(APIView):
    """
    Verify Apple In-App Purchase receipt and activate subscription
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AppleIAPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receipt_data = serializer.validated_data['receipt_data']
        product_id = serializer.validated_data.get('product_id')
        transaction_id = serializer.validated_data.get('transaction_id')
        
        try:
            # Check if Apple IAP is configured
            if not apple_iap_service.is_configured():
                return Response({
                    'error': 'Apple In-App Purchase is not configured. Please contact administrator.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check if transaction already processed
            if transaction_id:
                existing_payment = Payment.objects.filter(
                    apple_transaction_id=transaction_id
                ).first()
                
                if existing_payment and existing_payment.status == 'Success':
                    from subscriptionApp.serializers import SubscriptionDetailsSerializer
                    return Response({
                        'status': 'already_processed',
                        'message': 'This transaction has already been processed',
                        'payment': PaymentSerializer(existing_payment).data,
                        'subscription': SubscriptionDetailsSerializer(existing_payment.subscription).data if existing_payment.subscription else None
                    }, status=status.HTTP_200_OK)
            
            # Verify receipt with Apple
            receipt_response = apple_iap_service.verify_receipt(receipt_data)
            parsed_receipt = apple_iap_service.parse_receipt_response(receipt_response)
            
            # Verify bundle ID
            if not apple_iap_service.verify_bundle_id(parsed_receipt['bundle_id']):
                return Response({
                    'error': 'Invalid bundle ID. This receipt is not for this app.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find matching subscription plan by Apple product ID
            plan = SubscriptionPlansModel.objects.filter(
                apple_product_id=parsed_receipt['product_id'],
                is_active=True
            ).first()
            
            if not plan:
                return Response({
                    'error': f"No subscription plan found for product ID: {parsed_receipt['product_id']}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check for existing active subscription
            try:
                existing_subscription = SubscriptionDetails.objects.get(user=request.user)
                existing_subscription.check_and_update_status()
                
                if existing_subscription.is_active:
                    return Response({
                        'error': 'You already have an active subscription',
                        'expires_at': existing_subscription.expires_at,
                        'days_remaining': existing_subscription.days_remaining
                    }, status=status.HTTP_400_BAD_REQUEST)
            except SubscriptionDetails.DoesNotExist:
                pass
            
            # Create plan snapshot
            plan_snapshot = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'amount': float(plan.amount),
                'duration': plan.duration,
                'purchased_at': timezone.now().isoformat(),
                'payment_provider': 'apple_iap'
            }
            
            # Create or update subscription
            subscription, created = SubscriptionDetails.objects.get_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'plan_snapshot': plan_snapshot,
                    'is_active': False
                }
            )
            
            if not created:
                subscription.plan = plan
                subscription.plan_snapshot = plan_snapshot
                subscription.is_active = False
                subscription.save()
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                subscription=subscription,
                plan=plan,
                payment_provider='apple_iap',
                apple_transaction_id=parsed_receipt['transaction_id'],
                apple_original_transaction_id=parsed_receipt['original_transaction_id'],
                apple_product_id=parsed_receipt['product_id'],
                apple_receipt_data=receipt_data,
                apple_environment=parsed_receipt['environment'],
                amount=int(plan.amount * 100),  # Store in paise/cents for consistency
                currency='INR',  # Or get from plan
                status='Success',
                payment_method='apple_iap'
            )
            
            # Activate subscription
            subscription.activate_subscription()
            
            from subscriptionApp.serializers import SubscriptionDetailsSerializer
            return Response({
                'status': 'success',
                'message': 'Apple In-App Purchase verified and subscription activated',
                'payment': PaymentSerializer(payment).data,
                'subscription': SubscriptionDetailsSerializer(subscription).data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class AppleServerNotificationWebhookAPIView(APIView):
    """
    Handle Apple App Store Server Notifications V2
    Webhook endpoint for Apple to send server notifications
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle Apple Server Notifications
        https://developer.apple.com/documentation/appstoreservernotifications
        """
        try:
            notification_data = request.body.decode('utf-8')
            payload = json.loads(notification_data)
            
            notification_type = payload.get('notificationType')
            subtype = payload.get('subtype')
            
            # Log notification for debugging
            print(f"Apple Notification: {notification_type} - {subtype}")
            
            # Handle different notification types
            if notification_type == 'SUBSCRIBED':
                self.handle_subscribed(payload)
            elif notification_type == 'DID_RENEW':
                self.handle_renewal(payload)
            elif notification_type == 'EXPIRED':
                self.handle_expiration(payload)
            elif notification_type == 'DID_FAIL_TO_RENEW':
                self.handle_renewal_failure(payload)
            elif notification_type == 'REFUND':
                self.handle_refund(payload)
            elif notification_type == 'REVOKE':
                self.handle_revoke(payload)
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log error but return 200 to prevent Apple from retrying
            print(f"Apple webhook error: {str(e)}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)
    
    def handle_subscribed(self, payload):
        """Handle new subscription"""
        # In most cases, this is already handled by the verify endpoint
        # This webhook confirms the subscription
        pass
    
    def handle_renewal(self, payload):
        """Handle subscription renewal"""
        data = payload.get('data', {})
        transaction_info = data.get('transactionInfo', {})
        original_transaction_id = transaction_info.get('originalTransactionId')
        
        if original_transaction_id:
            # Find the original payment
            payment = Payment.objects.filter(
                apple_original_transaction_id=original_transaction_id
            ).first()
            
            if payment and payment.subscription:
                # Extend subscription
                subscription = payment.subscription
                subscription.activate_subscription()  # This will extend based on plan duration
    
    def handle_expiration(self, payload):
        """Handle subscription expiration"""
        data = payload.get('data', {})
        transaction_info = data.get('transactionInfo', {})
        original_transaction_id = transaction_info.get('originalTransactionId')
        
        if original_transaction_id:
            payment = Payment.objects.filter(
                apple_original_transaction_id=original_transaction_id
            ).first()
            
            if payment and payment.subscription:
                payment.subscription.deactivate_subscription()
    
    def handle_renewal_failure(self, payload):
        """Handle renewal failure - grace period"""
        # Subscription still active but renewal failed
        # You might want to notify the user
        pass
    
    def handle_refund(self, payload):
        """Handle refund - deactivate subscription"""
        data = payload.get('data', {})
        transaction_info = data.get('transactionInfo', {})
        original_transaction_id = transaction_info.get('originalTransactionId')
        
        if original_transaction_id:
            payment = Payment.objects.filter(
                apple_original_transaction_id=original_transaction_id
            ).first()
            
            if payment:
                payment.status = 'Refunded'
                payment.save()
                
                if payment.subscription:
                    payment.subscription.deactivate_subscription()
    
    def handle_revoke(self, payload):
        """Handle revoke - similar to refund"""
        self.handle_refund(payload)


# ============================================================================
# COMMON PAYMENT VIEWS
# ============================================================================

class PaymentHistoryAPIView(APIView):
    """
    Get user's payment history (both Razorpay and Apple IAP)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = Payment.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response({
            'payments': serializer.data
        }, status=status.HTTP_200_OK)


class PaymentConfigStatusAPIView(APIView):
    """
    Check if payment providers are configured
    Useful for debugging and admin monitoring
    Staff only endpoint
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only show this to staff/superusers
        if not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'razorpay': {
                'configured': bool(config.RAZORPAY_KEY_ID and config.RAZORPAY_KEY_SECRET),
                'has_webhook_secret': bool(config.RAZORPAY_WEBHOOK_SECRET),
                'key_id': config.RAZORPAY_KEY_ID[:10] + '***' if config.RAZORPAY_KEY_ID else None
            },
            'apple_iap': {
                'configured': apple_iap_service.is_configured(),
                'bundle_id': config.APPLE_BUNDLE_ID,
                'has_shared_secret': bool(config.APPLE_SHARED_SECRET),
                'has_api_credentials': bool(config.APPLE_ISSUER_ID and 
                                           config.APPLE_KEY_ID and 
                                           config.APPLE_PRIVATE_KEY)
            },
            'business': {
                'name': config.BUSINESS_NAME,
                'theme_color': config.RAZORPAY_THEME_COLOR
            }
        }, status=status.HTTP_200_OK)


# ============================================================================
# TEST/DEBUG VIEWS
# ============================================================================

class TestPaymentView(View):
    """
    Test page for Razorpay payment (web-based testing)
    """
    def get(self, request):
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Payment</title>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
<body style="font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto;">
    <h2>Test Razorpay Payment</h2>
    <button id="payBtn" style="padding: 12px 24px; font-size: 16px; background: #3399cc; color: white; border: none; border-radius: 5px; cursor: pointer;">Pay for Subscription</button>
    <div id="msg" style="margin-top: 20px; padding: 15px; border-radius: 5px;"></div>

    <script>
    (function() {
        'use strict';
        const AUTH_TOKEN = 'YOUR_TEST_TOKEN_HERE';  // Replace with valid token
        const btn = document.getElementById('payBtn');
        const msg = document.getElementById('msg');
        const API = window.location.origin;
        
        btn.addEventListener('click', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
            evt.stopImmediatePropagation();
            
            msg.innerHTML = 'Creating order...';
            msg.style.background = '#f0f0f0';
            
            fetch(API + '/payments/create-order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                credentials: 'include',
                body: JSON.stringify({ plan_id: 1 })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    msg.innerHTML = '❌ Error: ' + data.error;
                    msg.style.background = '#f8d7da';
                    return;
                }
                
                msg.innerHTML = 'Opening Razorpay...';
                
                const opts = {
                    key: data.key,
                    amount: data.amount,
                    currency: data.currency,
                    name: data.name,
                    description: data.description,
                    order_id: data.order_id,
                    prefill: data.prefill,
                    theme: data.theme,
                    handler: function(resp) {
                        msg.innerHTML = '✅ Payment Successful!';
                        msg.style.background = '#d4edda';
                    },
                    modal: {
                        ondismiss: function() {
                            msg.innerHTML = '⚠️ Payment Cancelled';
                            msg.style.background = '#fff3cd';
                        }
                    }
                };
                
                new Razorpay(opts).open();
            })
            .catch(err => {
                msg.innerHTML = '❌ Error: ' + err.message;
                msg.style.background = '#f8d7da';
            });
            
            return false;
        }, false);
    })();
    </script>
</body>
</html>
"""
        return HttpResponse(html)
