from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 
                       'webhook_event_id', 'created_at', 'updated_at']
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of payment records
        return False
