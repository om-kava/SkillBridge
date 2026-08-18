from django.shortcuts import render, redirect
from django.http import JsonResponse
import openai

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat

from django.utils import timezone


import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def ask_openai(message):
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    base_url = os.environ.get('OPENAI_BASE_URL', None)
    
    if not api_key or api_key == 'your-api-key':
        return "[Error: API Key is not set. Please set your OPENAI_API_KEY in the .env file.]"

    if api_key.startswith('sk-or-v1'):
        base_url = base_url or 'https://openrouter.ai/api/v1'
        model = "openai/gpt-3.5-turbo"
    else:
        model = "gpt-3.5-turbo"
    
    try:
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        client = OpenAI(**kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ]
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        error_msg = str(e)
        if "credit_balance_exhausted" in error_msg or "insufficient_quota" in error_msg or "429" in error_msg:
            return "[API Error: You have no credits remaining on this API key. Please check your billing details.]"
        return f"[API Error: {error_msg}]"

# Create your views here.
def chatbot(request):
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)
    else:
        chats = []

    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)

        if request.user.is_authenticated:
            chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
            chat.save()

        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Password dont match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')
