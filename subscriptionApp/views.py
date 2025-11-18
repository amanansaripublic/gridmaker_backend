from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionPlansModel, SubscriptionDetails
from .serializers import SubscriptionPlanSerializer, SubscriptionDetailsSerializer


class SubscriptionPlansListAPIView(APIView):
    """
    Get list of all active subscription plans
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        plans = SubscriptionPlansModel.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({
            'plans': serializer.data
        }, status=status.HTTP_200_OK)


class UserSubscriptionStatusAPIView(APIView):
    """
    Get current user's subscription status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = SubscriptionDetails.objects.get(user=request.user)
            # Check and update status if expired
            subscription.check_and_update_status()
            serializer = SubscriptionDetailsSerializer(subscription)
            
            return Response({
                'has_subscription': True,
                'subscription': serializer.data
            }, status=status.HTTP_200_OK)
            
        except SubscriptionDetails.DoesNotExist:
            return Response({
                'has_subscription': False,
                'subscription': None
            }, status=status.HTTP_200_OK)
