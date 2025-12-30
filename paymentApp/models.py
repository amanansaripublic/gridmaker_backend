# payments/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Payment(models.Model):
    PAYMENT_PROVIDER_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('apple_iap', 'Apple In-App Purchase'),
    ]
    
    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey('subscriptionApp.SubscriptionDetails', on_delete=models.SET_NULL, null=True, blank=True)
    plan = models.ForeignKey('subscriptionApp.SubscriptionPlansModel', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment provider
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, default='razorpay')
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Apple IAP fields
    apple_transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    apple_original_transaction_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    apple_product_id = models.CharField(max_length=100, blank=True, null=True)
    apple_receipt_data = models.TextField(blank=True, null=True)
    apple_environment = models.CharField(max_length=20, blank=True, null=True)  # Sandbox or Production
    
    amount = models.IntegerField()
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Created')
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_description = models.TextField(blank=True, null=True)
    
    webhook_event_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['apple_transaction_id']),
            models.Index(fields=['apple_original_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.payment_provider}"
