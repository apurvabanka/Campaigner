from django import forms
from .models import Campaign

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['title', 'description', 'start_date', 'end_date', 'reward_type', 'reward_amount', 'task_type']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reward_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

class ReferralForm(forms.Form):
    name = forms.CharField(max_length=255)
    emails = forms.CharField(widget=forms.Textarea)
    message = forms.CharField(widget=forms.Textarea, required=False)

    def clean_emails(self):
        emails = self.cleaned_data['emails']
        email_list = [email.strip() for email in emails.split('\n') if email.strip()]
        if not email_list:
            raise forms.ValidationError('Please enter at least one valid email address')
        return email_list

class OnboardingForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    referral_code = forms.CharField(max_length=100)