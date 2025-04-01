import csv
import re

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
        request_type = data.get('type', 'campaign')  # Default to campaign if not specified
        
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
        
        if request_type == 'chatbot':
            # For chatbot, return the raw response
            return JsonResponse({'response': generated_text})
        else:
            # For campaign generation, parse and validate JSON
            try:
                # Clean the response by removing markdown code block formatting
                if isinstance(generated_text, str):
                    if generated_text.startswith('```json'):
                        generated_text = generated_text[7:]
                    if generated_text.endswith('```'):
                        generated_text = generated_text[:-3]
                    generated_text = generated_text.strip()
                
                # Try to parse the response as JSON
                parsed_response = json.loads(generated_text)
                
                # Validate the response structure
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response must be a JSON object")
                
                if 'description' not in parsed_response:
                    raise ValueError("Response must include a 'description' field")
                
                if 'task_suggestions' not in parsed_response:
                    raise ValueError("Response must include a 'task_suggestions' field")
                
                task_suggestions = parsed_response['task_suggestions']
                if not isinstance(task_suggestions, dict):
                    raise ValueError("task_suggestions must be a JSON object")
                
                # Validate task suggestion types
                required_types = {'cash', 'discount', 'points', 'gift'}
                suggestion_types = set(task_suggestions.keys())
                if not required_types.issubset(suggestion_types):
                    raise ValueError("task_suggestions must include all required types: cash, discount, points, gift")
                
                # Validate suggestion formats
                for type_name, suggestion in task_suggestions.items():
                    if not isinstance(suggestion, str):
                        raise ValueError(f"Suggestion for {type_name} must be a string")
                    
                    # Validate amount format based on type
                    if type_name == 'cash' and not re.search(r'\$(\d+\.?\d*)', suggestion):
                        raise ValueError(f"Cash suggestion must include a dollar amount: {suggestion}")
                    elif type_name == 'discount' and not re.search(r'(\d+)%', suggestion):
                        raise ValueError(f"Discount suggestion must include a percentage: {suggestion}")
                    elif type_name == 'points' and not re.search(r'(\d+)\s+points', suggestion):
                        raise ValueError(f"Points suggestion must include a number of points: {suggestion}")
                    elif type_name == 'gift' and not re.search(r'\$(\d+\.?\d*)', suggestion):
                        raise ValueError(f"Gift suggestion must include a dollar amount: {suggestion}")
                
                return JsonResponse({'response': parsed_response})
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract fields using regex
                description_match = re.search(r'"description"\s*:\s*"([^"]+)"', generated_text)
                task_suggestions_match = re.search(r'"task_suggestions"\s*:\s*{([^}]+)}', generated_text)
                
                if not description_match or not task_suggestions_match:
                    return JsonResponse({'error': 'Failed to parse response format'}, status=500)
                
                description = description_match.group(1)
                task_suggestions_text = task_suggestions_match.group(1)
                
                # Extract individual suggestions
                task_suggestions = {}
                for type_name in ['cash', 'discount', 'points', 'gift']:
                    pattern = f'"{type_name}"\s*:\s*"([^"]+)"'
                    match = re.search(pattern, task_suggestions_text)
                    if match:
                        task_suggestions[type_name] = match.group(1)
                
                if not task_suggestions:
                    return JsonResponse({'error': 'Failed to extract task suggestions'}, status=500)
                
                return JsonResponse({
                    'response': {
                        'description': description,
                        'task_suggestions': task_suggestions
                    }
                })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
