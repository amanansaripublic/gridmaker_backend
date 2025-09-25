
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
    class Meta:
        model = UserDetailsModel
        fields = "__all__"

class UserConsumeCreditSerializer(serializers.Serializer):
    credits = serializers.IntegerField()