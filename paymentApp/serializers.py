from rest_framework import serializers
from .models import Payment


class CreateSubscriptionOrderSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    
    def validate_plan_id(self, value):
        from subscriptionApp.models import SubscriptionPlansModel
        try:
            plan = SubscriptionPlansModel.objects.get(id=value, is_active=True)
        except SubscriptionPlansModel.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan selected")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'razorpay_order_id', 'razorpay_payment_id', 'amount', 
                  'currency', 'status', 'plan_name', 'created_at']


class PaymentVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=255)
