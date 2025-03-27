import uuid
from django.db import models
from django.contrib.auth.models import User

class BusinessOwner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)

class Customer(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(BusinessOwner, on_delete=models.CASCADE)
    reward_points = models.IntegerField(default=0)
    referrals_sent = models.IntegerField(default=0)
    referrals_completed = models.IntegerField(default=0)
