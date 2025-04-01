import csv

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from campaigns.models import Campaign
from .models import BusinessOwner, Customer
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from io import TextIOWrapper
from .forms import BusinessOwnerForm, LoginForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import requests
from django.conf import settings

@login_required
def dashboard(request):
    owner = BusinessOwner.objects.get(user=request.user)
    customers = Customer.objects.filter(owner=owner)
    campaigns = Campaign.objects.filter(owner=owner)
    total_revenue = sum(customer.reward_points for customer in customers)
    total_referrals = sum(customer.referrals_sent for customer in customers)
    return render(request, 'accounts/dashboard.html', {
        'owner': owner, 
        'customers': customers, 
        'campaigns': campaigns,
        'total_revenue': total_revenue,
        'total_referrals': total_referrals
    })

@login_required
def add_customer(request):
    if request.method == 'POST':
        email = request.POST['email']
        name = request.POST['name']
        owner = BusinessOwner.objects.get(user=request.user)
        Customer.objects.create(email=email, name=name, owner=owner)
        return redirect('dashboard')
    return render(request, 'accounts/add_customer.html')

@login_required
def bulk_upload_customers(request):
    if request.method == 'POST':
        csv_file = request.FILES['file']
        owner = BusinessOwner.objects.get(user=request.user)
        csv_reader = csv.reader(TextIOWrapper(csv_file, encoding='utf-8'))
        for row in csv_reader:
            email, name = row
            Customer.objects.create(email=email, name=name, owner=owner)
        return redirect('dashboard')
    return render(request, 'accounts/bulk_upload_customers.html')

def register_or_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        if 'register' in request.POST:
            form = BusinessOwnerForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    email=form.cleaned_data['email']
                )
                BusinessOwner.objects.create(
                    user=user,
                    business_name=form.cleaned_data['business_name']
                )
                login(request, user)
                return redirect('dashboard')
        elif 'login' in request.POST:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                user = authenticate(
                    username=login_form.cleaned_data['username'],
                    password=login_form.cleaned_data['password']
                )
                if user is not None:
                    login(request, user)
                    return redirect('dashboard')
    else:
        form = BusinessOwnerForm()
        login_form = LoginForm()
    return render(request, 'accounts/register_or_login.html', {'form': form, 'login_form': login_form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('register_or_login')

@require_http_methods(["POST"])
def generate_ai_response(request):
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
        
        if not prompt:
            return JsonResponse({'error': 'No prompt provided'}, status=400)
        
        # Make request to Gemini API
        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': settings.GEMINI_API_KEY
            },
            json={
                'contents': [{
                    'parts': [{
                        'text': prompt
                    }]
                }]
            }
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'API request failed'}, status=response.status_code)
        
        response_data = response.json()
        generated_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        return JsonResponse({'response': generated_text})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
