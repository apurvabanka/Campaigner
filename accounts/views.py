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
from django.contrib import messages
from django.db.utils import IntegrityError

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
        
        # Get headers and find name and email column indices
        headers = next(csv_reader)
        headers = [h.lower() for h in headers]
        
        try:
            name_index = next(i for i, h in enumerate(headers) if 'name' in h)
            email_index = next(i for i, h in enumerate(headers) if 'email' in h)
        except StopIteration:
            messages.error(request, 'CSV file must contain name and email columns')
            return redirect('bulk_upload_customers')
        
        # Process each row
        skipped_emails = []
        created_count = 0
        
        for row in csv_reader:
            if len(row) > max(name_index, email_index):
                name = row[name_index].strip()
                email = row[email_index].strip()
                if name and email:  # Only process if both fields are non-empty
                    try:
                        Customer.objects.create(email=email, name=name, owner=owner)
                        created_count += 1
                    except IntegrityError:
                        skipped_emails.append(email)
        
        # Prepare success message with details
        message = f'Successfully uploaded {created_count} customers.'
        if skipped_emails:
            message += f' Skipped {len(skipped_emails)} duplicate emails.'
            if len(skipped_emails) <= 5:  # Show up to 5 duplicate emails
                message += f' Duplicates: {", ".join(skipped_emails)}'
            else:
                message += f' First 5 duplicates: {", ".join(skipped_emails[:5])}...'
        
        messages.success(request, message)
        return redirect('dashboard')
    return render(request, 'accounts/bulk_upload_customers.html')

def register_or_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = BusinessOwnerForm()
    login_form = LoginForm()
    
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
                    login_form.add_error(None, 'Incorrect username or password')
    
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

def ai_campaign_assistant(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        
        # Create a structured prompt for the AI
        ai_prompt = f"""
        Create a marketing campaign based on this request: "{prompt}"
        
        Generate a response in the following JSON format:
        {{
            "campaign": {{
                "title": "A catchy, concise campaign title",
                "description": "A compelling description that explains the campaign benefits and mechanics",
                "reward_type": "One of: cash, discount, points, gift",
                "duration": "Number of days the campaign should run (e.g.,7, 10, 15, 30)",
                "reward_amount": "The amount of the reward (e.g., 10, 20, 30)",
                "task_type": "One of: quiz, purchase, event"
            }},
            
        }}
        
        Make sure the response is valid JSON and includes all required fields.
        The title should be catchy and memorable.
        The description should be clear and engaging.
        The reward type should match the user's request or suggest the most appropriate type.
        The duration should be reasonable for the campaign type.
        """

        try:
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
                            'text': ai_prompt
                        }]
                    }]
                }
            )
            
            if response.status_code != 200:
                return JsonResponse({'error': 'API request failed'}, status=response.status_code)
            
            # print(response.json())
            
            response_data = response.json()
            generated_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            print(generated_text + "1")

            generated_text = generated_text.replace('```json', '').replace('```', '')
            generated_text = generated_text.strip()
            

            print(generated_text)
            # Try to parse the response as JSON
            try:
                parsed_response = json.loads(generated_text)
                
                # Validate the response structure
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response must be a JSON object")
                
                if 'campaign' not in parsed_response:
                    raise ValueError("Response must include a 'campaign' object")
                
                campaign = parsed_response['campaign']
                required_fields = ['title', 'description', 'reward_type', 'duration']
                
                for field in required_fields:
                    if field not in campaign:
                        raise ValueError(f"Campaign must include '{field}' field")
                
                # Convert duration to integer if it's a string
                if isinstance(campaign['duration'], str):
                    campaign['duration'] = int(''.join(filter(str.isdigit, campaign['duration'])))
                
                return JsonResponse({'response': json.dumps(parsed_response)})
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                return JsonResponse({'response': "I couldn't create a valid campaign structure. Please try again with more specific details."})
            except ValueError as e:
                print(f"Validation error: {str(e)}")
                return JsonResponse({'response': "The campaign structure was incomplete. Please try again with all required details."})
            
        except Exception as e:
            print(f"Error in ai_campaign_assistant: {str(e)}")
            return JsonResponse({'response': "I encountered an error while creating your campaign. Please try again."})
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_ai_campaign_response(prompt, current_step):
    # Different logics for different steps
    try:
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
            return f"Error: API request failed with status {response.status_code}"
        
        response_data = response.json()
        generated_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        # Clean the response by removing markdown code block formatting
        if isinstance(generated_text, str):
            # Remove ```json at the start if present
            if generated_text.startswith('```json'):
                generated_text = generated_text[7:]
            # Remove any ``` at the end
            generated_text = re.sub(r'```$', '', generated_text)
            generated_text = generated_text.strip()
        
        # Log the cleaned response for debugging
        print(f"Cleaned response: {generated_text}")
        
        # Try to parse the response as JSON
        try:
            parsed_response = json.loads(generated_text)
            print(f"Parsed response: {parsed_response}")
            
            if isinstance(parsed_response, dict) and 'suggestions' in parsed_response:
                suggestions = parsed_response['suggestions']
                
                if current_step == 'businessType':
                    response_text = "Based on your business type, here are some campaign suggestions:<br><br>"
                    for i, suggestion in enumerate(suggestions, 1):
                        if isinstance(suggestion, dict) and 'name' in suggestion and 'description' in suggestion:
                            response_text += f"{i}. {suggestion['name']}<br>"
                            # response_text += f"   {suggestion['description']}<br><br>"
                    response_text += "Please select one of these campaign names or suggest your own. Respond with the Title of the campaign you want to create."
                
                elif current_step == 'campaignTitle':
                    response_text = "For your campaign, here are some reward type suggestions:<br><br>"
                    for i, suggestion in enumerate(suggestions, 1):
                        if isinstance(suggestion, dict) and 'type' in suggestion and 'description' in suggestion:
                            response_text += f"{i}. {suggestion['type']} <br>"
                            # response_text += f"   {suggestion['description']}<br><br>"
                    response_text += "Please select one of these reward types or suggest your own. Make sure to respond with the Reward Type you want to create."
                
                elif current_step == 'rewardType':
                    response_text = "For your reward type, here are some duration suggestions:<br><br>"
                    for i, suggestion in enumerate(suggestions, 1):
                        if isinstance(suggestion, dict) and 'duration' in suggestion and 'description' in suggestion:
                            response_text += f"{i}. {suggestion['duration']} days<br>"
                            response_text += f"   {suggestion['description']}<br><br>"
                    response_text += "Please select one of these durations or suggest your own. Make sure to respond with the Duration of the campaign you want to create."
                
                return response_text
            else:
                print(f"Invalid response structure: {parsed_response}")
                # return "I apologize, but I couldn't generate appropriate suggestions. Please try again with a different input."
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print(f"Failed to parse text: {generated_text}")
            # return "I apologize, but I couldn't process the response properly. Please try again."
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in generate_ai_campaign_response: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."
