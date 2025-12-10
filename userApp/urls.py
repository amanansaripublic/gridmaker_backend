
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserDetailsModelViewSet, DeleteAccoutAPIView

router = DefaultRouter()
router.register(r'details', UserDetailsModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('delete/', DeleteAccoutAPIView.as_view())
]
