from django.contrib import admin

from django.contrib import admin
from .models import BusinessOwner, Customer

# Register your models here.
admin.site.register(BusinessOwner)
admin.site.register(Customer)