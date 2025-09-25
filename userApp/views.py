from django.shortcuts import render

# Create your views here.

from customCalsses.CustomBaseModelViewSet import CustomBaseModelViewSet
from .models import UserDetailsModel
from .serializers import UserDetialsModelSerializer
from helpers.PaginationClass import CustomPageNumberPagination
from customCalsses.BaseFilterSet import BaseFilterSet
from .filters import UserDetailsModelFilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UserConsumeCreditSerializer

class UserDetailsModelViewSet(CustomBaseModelViewSet):
    queryset = UserDetailsModel.objects.all()
    serializer_class = UserDetialsModelSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserDetailsModelFilterSet
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        # only return objects belonging to the logged-in user
        return UserDetailsModel.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.get(user=request.user.id)
        serializer = self.get_serializer(queryset)
        return Response({"result": serializer.data})
    
    # Custom endpoint: /api/user-details/current/
    # @action(detail=False, methods=['get'])
    # def current(self, request):
    #     user_details = self.get_queryset().first()
    #     if user_details:
    #         serializer = self.get_serializer(user_details)
    #         return Response(serializer.data)
    #     return Response({"message": "No details found"}, status=status.HTTP_404_NOT_FOUND)

    # Custom endpoint: /api/user-details/update_name/
    @action(detail=False, methods=['post'], url_path='consume_credit')
    def consume_credit(self, request, pk=None):
        instance = self.get_queryset().get(user=request.user)
        serializer = UserConsumeCreditSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        credits = serializer.data["credits"]
        if instance.credits < credits :
            return Response({"message" : "Not enough credits !!"}, status = status.HTTP_400_BAD_REQUEST)
        # instance.cerdits = instance.credits - credits
        # instance.save()
        obj = UserDetailsModel.objects.get(user=request.user)
        obj.credits = instance.credits - credits
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
        


        