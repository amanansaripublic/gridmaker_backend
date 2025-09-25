from django.urls import path

from .views import RequestRegisterationAPI, VerifyRegisterationAPI
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("registeration-request/", RequestRegisterationAPI.as_view()),
    path("registeration-confirm/", VerifyRegisterationAPI.as_view()),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
