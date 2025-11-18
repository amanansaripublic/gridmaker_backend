from django.contrib import admin
from .models import SubscriptionPlansModel, SubscriptionDetails


@admin.register(SubscriptionPlansModel)
class SubscriptionPlansAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(SubscriptionDetails)
class SubscriptionDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'starts_at', 'expires_at', 'days_remaining']
    list_filter = ['is_active', 'plan', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['purchased_at', 'created_at', 'updated_at', 'days_remaining', 'is_expired']
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Remaining'
