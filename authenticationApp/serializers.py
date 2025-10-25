

from rest_framework import serializers
from .models import OTPVerificationModel
from userApp.models import UserDetailsModel
from userApp.serializers import UserDetialsModelSerializer

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
    phone_number = serializers.CharField(max_length=200)
    name = serializers.CharField(max_length=256)

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField()
    otp = serializers.CharField()
    token = serializers.CharField(max_length=600)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get user details from UserdetailsModel
        try:
            userDetails = UserDetailsModel.objects.get(user=self.user)
            userDetailsSerializer = UserDetialsModelSerializer(userDetails)
            data['user_details'] = userDetailsSerializer.data
        except UserDetailsModel.DoesNotExist:
            data['user_details'] = None
        
        return data
    
class CustomTokenRefreshSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get user details from UserdetailsModel
        try:
            userDetails = UserDetailsModel.objects.get(user=self.user)
            userDetailsSerializer = UserDetialsModelSerializer(userDetails)
            data['user_details'] = userDetailsSerializer.data
        except UserDetailsModel.DoesNotExist:
            data['user_details'] = None
        
        return data

# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
        
#         # Get user details
#         try:
#             userDetails = UserDetailsModel.objects.get(user=self.user)
#             userDetailsSerializer = UserDetialsModelSerializer(userDetails)
#             data['user_details'] = userDetailsSerializer.data
#         except UserDetailsModel.DoesNotExist:
#             data['user_details'] = None
        
#         return data