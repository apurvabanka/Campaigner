from django.contrib import admin

from django.contrib import admin
from .models import Campaign, CampaignCustomer, Referral

# Register your models here.
admin.site.register(Campaign)
admin.site.register(Referral)
admin.site.register(CampaignCustomer)