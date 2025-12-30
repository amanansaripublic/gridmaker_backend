from django.conf import settings
import razorpay


class RazorpayService:
    """Centralized Razorpay service"""
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount, currency='INR', notes=None):
        """Create Razorpay order"""
        return self.client.order.create({
            'amount': amount,
            'currency': currency,
            'payment_capture': '0',
            'notes': notes or {}
        })
    
    def verify_signature(self, params_dict):
        """Verify payment signature"""
        return self.client.utility.verify_payment_signature(params_dict)
    
    def capture_payment(self, payment_id, amount):
        """Capture payment"""
        return self.client.payment.capture(payment_id, amount)
    
    def verify_webhook_signature(self, body, signature, secret):
        """Verify webhook signature"""
        return self.client.utility.verify_webhook_signature(body, signature, secret)
    
    def refund_payment(self, payment_id, amount=None):
        """Refund payment"""
        if amount:
            return self.client.payment.refund(payment_id, amount)
        return self.client.payment.refund(payment_id)
    
    def fetch_order(self, order_id):
        """Fetch order details from Razorpay"""
        return self.client.order.fetch(order_id)
    
    def fetch_order_payments(self, order_id):
        """Fetch all payments for an order"""
        return self.client.order.payments(order_id)
    
    def fetch_payment(self, payment_id):
        """Fetch payment details"""
        return self.client.payment.fetch(payment_id)


# Create a global instance
razorpay_service = RazorpayService()
