from django.db import models
from django.contrib.auth.models import User
# Create your models here.



class UserDetailsModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, null=True, blank=True)
    grid_credits = models.IntegerField(default=3, null=True, blank=True)
    carousel_credits = models.IntegerField(default=3, null=True, blank=True)
    phone_number = models.CharField(max_length=200)
    email = models.EmailField()