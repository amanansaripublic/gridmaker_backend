
from rest_framework import serializers

from .models import UserDetailsModel
from django.contrib.auth.models import User
from customCalsses.CustomBaseModelSerializer import CustomBaseModelSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id','username', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserDetialsModelSerializer(CustomBaseModelSerializer):
    subscription_details = serializers.SerializerMethodField()
    class Meta:
        model = UserDetailsModel
        fields = "__all__"
    
    def get_subscription_details(self, obj):
        from subscriptionApp.models import SubscriptionDetails
        from subscriptionApp.serializers import SubscriptionDetailsSerializer
        if SubscriptionDetails.objects.filter(user = obj.user):
            subscriptionDetails = SubscriptionDetails.objects.get(user=obj.user)
            subscriptionDetails = SubscriptionDetailsSerializer(subscriptionDetails)
            return subscriptionDetails.data
        return None

class UserConsumeCreditSerializer(serializers.Serializer):
    grid_credits = serializers.IntegerField(required=False, min_value=0)
    carousel_credits = serializers.IntegerField(required=False, min_value=0)