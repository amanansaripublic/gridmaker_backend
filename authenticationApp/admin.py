from django.contrib import admin

# Register your models here.

from .models import OTPVerificationModel

admin.site.register(OTPVerificationModel)