from django.db import models

# Create your models here.

import random


class OTPVerificationModel(models.Model):
    class OTPMethods(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
    
    class Purposes(models.TextChoices):
        REGISTRATION = 'REGISTRATION', 'Registration'
    
    token = models.UUIDField()
    opt_method = models.CharField(max_length=256, choices=OTPMethods.choices)
    otp_value = models.CharField(max_length=256)
    purpose = models.CharField(max_length=256, choices=Purposes.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()


    def generate_otp(length=4):
        otp_chars = "0123456789"
        # return ''.join(random.choice(otp_chars) for _ in range(length))
        return '1234'
    
    def VerifyOTP(self, otp):
        if otp == self.otp_value:
            return True
        return False
    
    def __str__(self):
        return f"OTP : {self.otp_value}"