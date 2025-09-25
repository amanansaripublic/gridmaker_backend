

from rest_framework import serializers
from .models import OTPVerificationModel

class RequestRegisterationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerificationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerificationModel
        fields = "__all__"
    
class VerifyRegistrationSerializer(serializers.Serializer):
    password = serializers.CharField()
    otp = serializers.CharField()
    token = serializers.CharField(max_length=600)
    