from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RequestRegisterationSerializer, OTPVerificationModelSerializer, VerifyRegistrationSerializer
from django.conf import settings
from django.core.mail import send_mail
from appbackend import AllUtils
from rest_framework import status
from .models import OTPVerificationModel
import uuid
from  django.contrib.auth.models import User
from userApp.serializers import UserDetialsModelSerializer, UserSerializer
from userApp.models import UserDetailsModel

class RequestRegisterationAPI(APIView):

    def post(self, request):
        data = request.data
        serializer = RequestRegisterationSerializer(data=data)
        if serializer.is_valid():
            otp = OTPVerificationModel.generate_otp()
            email = data['email']
            subject = "Registration OTP"
            message = f"This is a OTP for verification at app {otp}"
            if User.objects.filter(username=email):
                return Response({"message":"User with email already exist"})
            if AllUtils.sendMail(email, message, subject):
                
                token = uuid.uuid4()

                otpSerializer = OTPVerificationModelSerializer(data={
                    "token" : token,
                    "opt_method" : OTPVerificationModel.OTPMethods.EMAIL,
                    "otp_value" : otp,
                    "purpose" : OTPVerificationModel.Purposes.REGISTRATION,
                    "email" : email
                })
                if otpSerializer.is_valid():
                    otpSerializer.save()
                    return Response(
                        {
                            "token" : token
                        }, 
                        status=status.HTTP_200_OK
                        )
                else :
                    return Response(otpSerializer.errors)
            return Response({"msg":"Fail"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors)
    


class VerifyRegisterationAPI(APIView):
    def post(self, request):
        data = request.data
        serializer = VerifyRegistrationSerializer(data=data)
        if serializer.is_valid():
            token = data['token']
            otp = data['otp']
            password = data['password']
            print(password)
            if OTPVerificationModel.objects.filter(token=token, opt_method=OTPVerificationModel.OTPMethods.EMAIL, purpose=OTPVerificationModel.Purposes.REGISTRATION).exists() == False:
                return Response({"message": "OTP either used / expired"}, status=status.HTTP_400_BAD_REQUEST)
            otpModel = OTPVerificationModel.objects.get(token=token)
            if otpModel.VerifyOTP(otp):
                email = otpModel.email
                user_serializer = UserSerializer(data={
                    "username" : email,
                    "password" : password
                })
                if user_serializer.is_valid() == False :
                    return Response(user_serializer.errors)
                user = user_serializer.save()
                userDetails = UserDetailsModel(user=user)
                userDetails.save()
                otpModel.delete()
                # Generate access token
                from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
                access_token = AccessToken.for_user(user)

                # Generate refresh token
                refresh_token = RefreshToken.for_user(user)
                
                return Response({
                    'access': str(access_token),
                    'refresh': str(refresh_token),
                }, status=status.HTTP_201_CREATED)
            
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        