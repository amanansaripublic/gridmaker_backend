from rest_framework import serializers
from .models import SubscriptionPlansModel, SubscriptionDetails


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    amount_in_paise = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlansModel
        fields = ['id', 'name', 'description', 'amount', 'amount_in_paise', 'duration', 'is_active']
    
    def get_amount_in_paise(self, obj):
        return obj.get_amount_in_paise()


class SubscriptionDetailsSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    days_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SubscriptionDetails
        fields = ['id', 'plan', 'plan_details', 'plan_snapshot', 'purchased_at', 
                  'starts_at', 'expires_at', 'is_active', 'days_remaining', 'is_expired']
        read_only_fields = ['purchased_at', 'starts_at', 'expires_at', 'is_active']
