
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserDetailsModelViewSet

router = DefaultRouter()
router.register(r'details', UserDetailsModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
