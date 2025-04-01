from django import forms
from .models import Campaign

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['title', 'description', 'start_date', 'end_date', 'reward_type', 'reward_amount']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reward_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

class ReferralForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()

class OnboardingForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    referral_code = forms.CharField(max_length=100)