import uuid
from django.http import BadHeaderError, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import BusinessOwner, Customer
from campaigns.forms import CampaignForm, OnboardingForm, ReferralForm
from .models import Campaign, CampaignCustomer, Referral
from django.core.mail import send_mail

@login_required
def create_campaign(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            business_owner = BusinessOwner.objects.get(user=request.user)
            campaign.owner = business_owner
            campaign.save()
        
            customers = Customer.objects.filter(owner=business_owner)
            for customer in customers:
                campaign_customer = CampaignCustomer.objects.create(
                    campaign=campaign,
                    customer=customer,
                    referral_code=uuid.uuid4()
                )
                try:
                    send_mail(
                        'New Campaign Referral',
                        f'Hello {customer.name},\n\nYou have been referred to a new campaign: {campaign.title}.\nYour referral code is: {campaign_customer.referral_code}.\n\n Use this link to refer new individuals and claim your reward - http://127.0.0.1:8000/refer_customer/{campaign_customer.referral_code}\n\nBest regards,\n{business_owner.business_name}',
                        business_owner.user.email,
                        [customer.email],
                        fail_silently=False,
                    )
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                except Exception as e:
                    return HttpResponse(f'An error occurred: {e}')
            return redirect('dashboard')
    else:
        form = CampaignForm()
    return render(request, 'campaigns/create_campaign.html', {'form': form})

@login_required
def campaign_list(request):
    owner = BusinessOwner.objects.get(user=request.user)
    campaigns = Campaign.objects.filter(owner=owner)
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})

@login_required
def assign_customer(request, campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)
    if request.method == 'POST':
        customer_id = request.POST['customer_id']
        customer = Customer.objects.get(id=customer_id)
        referral_code = request.POST['referral_code']
        CampaignCustomer.objects.create(campaign=campaign, customer=customer, referral_code=referral_code)
        return redirect('campaign_list')
    customers = Customer.objects.filter(owner=campaign.owner)
    return render(request, 'campaigns/assign_customer.html', {'campaign': campaign, 'customers': customers})

@login_required
def analytics_view(request):
    owner = BusinessOwner.objects.get(user=request.user)
    customers = Customer.objects.filter(owner=owner)
    referrals = Referral.objects.filter(customer__in=customers)
    return render(request, 'campaigns/analytics.html', {'customers': customers, 'referrals': referrals})

def refer_customer(request, referral_code):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            referred_email = form.cleaned_data['email']
            try:
                campaign_customer = CampaignCustomer.objects.get(referral_code=referral_code)
                # referred_customer = Customer.objects.create(
                #     email=referred_email,
                #     name=form.cleaned_data['name'],
                #     owner=campaign_customer.customer.owner
                # )
                Referral.objects.create(
                    customer=campaign_customer.customer,
                    campaign=campaign_customer.campaign,
                    referred_email=referred_email
                )
                # Reward the referring customer
                campaign_customer.customer.referrals_sent += 1
                campaign_customer.customer.save()
                
                # Send email to the referred individual
                try:
                    send_mail(
                        'You have been referred!',
                        f'Hello {form.cleaned_data["name"]},\n\nYou have been referred to join our campaign: {campaign_customer.campaign.title}.\n\nPlease use the referral code to get onboarded {campaign_customer.referral_code}.\n\n You can use this link to compelte the onboarding process. http://127.0.0.1:8000/onboard/ \n\nBest regards,\n{campaign_customer.customer.owner.business_name}',
                        'apurvabanka1712@gmail.com',
                        [referred_email],
                        fail_silently=False,
                    )
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                except Exception as e:
                    return HttpResponse(f'An error occurred: {e}')
                
                return redirect('thank_you')
            except CampaignCustomer.DoesNotExist:
                return HttpResponse('Invalid referral code.')
    else:
        form = ReferralForm()
    return render(request, 'campaigns/refer_customer.html', {'form': form, 'referral_code': referral_code})

def thank_you(request):
    return render(request, 'campaigns/thank_you.html')

def onboarding(request):
    if request.method == 'POST':
        form = OnboardingForm(request.POST)
        if form.is_valid():
            try:
                campaign_customer = CampaignCustomer.objects.get(referral_code=form.cleaned_data['referral_code'])
                referred_customer = Customer.objects.create(
                    email=form.cleaned_data['email'],
                    name=form.cleaned_data['name'],
                    owner=campaign_customer.customer.owner
                )
                campaign_customer.customer.referrals_completed += 1
                campaign_customer.customer.reward_points += 10
                campaign_customer.customer.save()

                new_referral_code = str(uuid.uuid4())

                # Create a new CampaignCustomer for the referred customer
                new_campaign_customer = CampaignCustomer.objects.create(
                    customer=referred_customer,
                    campaign=campaign_customer.campaign,
                    referral_code=new_referral_code
                )
                
                # Send email to the new customer with their referral code
                try:
                    send_mail(
                        'Welcome to the campaign!',
                        f'Hello {referred_customer.name},\n\nWelcome to our campaign: {campaign_customer.campaign.title}.\n\n Your referral code is: {new_campaign_customer.referral_code}\n\n Use this link to refer new individuals and claim your reward - http://127.0.0.1:8000/refer_customer/{new_campaign_customer.referral_code} \n\nBest regards,\n{campaign_customer.customer.owner.business_name}',
                        'apurvabanka1712@gmail.com',
                        [referred_customer.email],
                        fail_silently=False,
                    )
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                except Exception as e:
                    return HttpResponse(f'An error occurred: {e}')
                
                return redirect('thank_you')
            except CampaignCustomer.DoesNotExist:
                return HttpResponse('Invalid referral code.')
    else:
        form = OnboardingForm()
    return render(request, 'campaigns/onboarding.html', {'form': form})