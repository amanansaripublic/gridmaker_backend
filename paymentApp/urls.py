from django.urls import path
from .views import (
    CreateSubscriptionOrderAPIView,
    VerifySubscriptionPaymentAPIView,
    PaymentHistoryAPIView,
    SubscriptionWebhookAPIView,
    TestPaymentView,
    RefreshPaymentStatusAPIView,
    CheckOrderStatusAPIView
)

app_name = 'payments'

urlpatterns = [
    path('create-order/', CreateSubscriptionOrderAPIView.as_view(), name='create_order'),
    path('verify/', VerifySubscriptionPaymentAPIView.as_view(), name='verify_payment'),
    path('history/', PaymentHistoryAPIView.as_view(), name='payment_history'),
    path('webhook/', SubscriptionWebhookAPIView.as_view(), name='webhook'),
    path('test/', TestPaymentView.as_view(), name='test_payment'),
     path('refresh-status/', RefreshPaymentStatusAPIView.as_view(), name='refresh_payment_status'),
    path('check-status/<str:order_id>/', CheckOrderStatusAPIView.as_view(), name='check_order_status')
]
