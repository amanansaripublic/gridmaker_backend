from django.contrib import admin

# Register your models here.

from .models import UserDetailsModel

admin.site.register(UserDetailsModel)