from django.db import models
from django.contrib.auth.models import User
from subscriptionApp.models import SubscriptionPlansModel, SubscriptionDetails


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Created', 'Created'),
        ('Authorized', 'Authorized'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(
        SubscriptionDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payments'
    )
    plan = models.ForeignKey(
        SubscriptionPlansModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    amount = models.IntegerField(help_text="Amount in paise")
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='Created')
    
    webhook_event_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    payment_method = models.CharField(max_length=50, blank=True, null=True)
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def __str__(self):
        return f"{self.user.username} - {self.razorpay_order_id} - {self.status}"
