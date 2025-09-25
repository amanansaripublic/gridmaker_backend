from django.db import models
from django.contrib.auth.models import User
# Create your models here.



class UserDetailsModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    credits = models.IntegerField(default=3, null=True, blank=True)