import uuid
from django.db import models
from accounts.models import BusinessOwner, Customer

class Campaign(models.Model):
    owner = models.ForeignKey(BusinessOwner, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()

# Customer that are part of a campaign
class CampaignCustomer(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)

# Individual referrals
class Referral(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    referred_email = models.EmailField()
    referral_code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
