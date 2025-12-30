# payments/admin.py
from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_provider', 'status', 'amount', 'created_at']
    list_filter = ['payment_provider', 'status', 'created_at']
    search_fields = ['user__username', 'razorpay_order_id', 'apple_transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'subscription', 'plan', 'payment_provider', 'status')
        }),
        ('Razorpay Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'),
            'classes': ('collapse',)
        }),
        ('Apple IAP Details', {
            'fields': ('apple_transaction_id', 'apple_original_transaction_id', 
                      'apple_product_id', 'apple_environment'),
            'classes': ('collapse',)
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'payment_method', 'error_code', 'error_description')
        }),
        ('Metadata', {
            'fields': ('webhook_event_id', 'created_at', 'updated_at')
        }),
    )
