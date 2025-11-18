from django.urls import path
from .views import (
    SubscriptionPlansListAPIView,
    UserSubscriptionStatusAPIView,
)

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', SubscriptionPlansListAPIView.as_view(), name='subscription_plans'),
    path('status/', UserSubscriptionStatusAPIView.as_view(), name='subscription_status'),
]
