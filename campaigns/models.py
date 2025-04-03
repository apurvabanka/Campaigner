import uuid
from django.db import models
from accounts.models import BusinessOwner, Customer

class Campaign(models.Model):
    TASK_TYPE_CHOICES = [
        ('referral', 'Referral'),
        ('quiz', 'Quiz or Trivia'),
        ('purchase', 'Make a Purchase'),
        ('event', 'Attend an Event'),
    ]
    
    owner = models.ForeignKey(BusinessOwner, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    reward_type = models.CharField(max_length=20, choices=[
        ('cash', 'Cash Reward'),
        ('discount', 'Discount Amount'),
        ('points', 'Reward Points'),
        ('gift', 'Gift Card')
    ], default='cash')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='referral')

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
