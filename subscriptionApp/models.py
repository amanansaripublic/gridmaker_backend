from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlansModel(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
    
    def __str__(self):
        return f"{self.name} - ₹{self.amount} for {self.duration} days"
    
    def get_amount_in_paise(self):
        """Convert amount to paise for Razorpay"""
        return int(self.amount * 100)


class SubscriptionDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlansModel, on_delete=models.SET_NULL, null=True, blank=True)
    plan_snapshot = models.JSONField(help_text="Snapshot of plan details at purchase time")
    
    purchased_at = models.DateTimeField(auto_now_add=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=False)
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription Detail"
        verbose_name_plural = "Subscription Details"
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
    
    @property
    def is_expired(self):
        """Check if subscription has expired"""
        if not self.expires_at:
            return True
        return timezone.now() > self.expires_at
    
    @property
    def days_remaining(self):
        """Calculate remaining days"""
        if not self.expires_at or self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)
    
    def activate_subscription(self):
        """Activate the subscription"""
        if self.plan and self.plan_snapshot:
            self.starts_at = timezone.now()
            self.expires_at = self.starts_at + timedelta(days=self.plan_snapshot['duration'])
            self.is_active = True
            self.save()
    
    def deactivate_subscription(self):
        """Deactivate the subscription"""
        self.is_active = False
        self.save()
    
    def check_and_update_status(self):
        """Check expiry and update status"""
        if self.is_active and self.is_expired:
            self.deactivate_subscription()
            return False
        return self.is_active
