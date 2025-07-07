from django.shortcuts import render, redirect
from django.db.models import Q
from news.models import News
from blog.models import BlogPost
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
from django.conf import settings
from django.contrib import messages
from .models import NewsletterSubscription
from mcq.models import MCQQuestion, MCQOption
import random
from django.core.mail import send_mail
import os
import json
import random


def home(request):
    # 🔹 Latest blogs
    latest_blogs = BlogPost.objects.all().order_by('-published_date')[:4]

    # 🔹 Load latest news from local JSON
    news_json_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'kathmandu_post_latest_updates.json')
    top_latest_news = []
    headline_for_video = None

    try:
        with open(news_json_path, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
            top_latest_news = news_data[:4]
            # ✅ Random headline for video
            headline_for_video = random.choice(news_data[:5])['title'] if news_data else None
    except FileNotFoundError:
        print("News JSON file not found.")

    # 🔹 Load MCQ question
    available_questions = MCQQuestion.objects.filter(is_active=True)
    if available_questions.exists():
        question = random.choice(list(available_questions))
        options = question.options.all()
    else:
        question = None
        options = None

    # 🔹 Get YouTube video for the chosen headline
    video_url = None
    try:
        if headline_for_video:
            youtube_api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={headline_for_video}&key={settings.YOUTUBE_API_KEY}&type=video&maxResults=5"
            yt_response = requests.get(youtube_api_url)
            yt_data = yt_response.json()
            items = yt_data.get('items', [])
            if items:
                video_id = random.choice(items)['id']['videoId']
                video_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
    except Exception as e:
        print("Error fetching YouTube video:", e)

    # 🔹 Final context
    context = {
        'latest_blogs': latest_blogs,
        'top_latest_news': top_latest_news,
        'question': question,
        'options': options,
        'username': request.user.username if request.user.is_authenticated else None,
        'breaking_video_url': video_url
    }

    return render(request, 'home.html', context)

def about(request):
    return render(request, 'core/about.html')



def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject', 'New Contact Message')
        message = request.POST.get('message')

        if name and email and message:
            full_message = f"From: {name} <{email}>\n\n{message}"

            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_RECEIVER_EMAIL],  # Or your preferred recipient
                fail_silently=False,
            )

            messages.success(request, 'Thank you for your message. We will get back to you soon!')
            return redirect('core:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')
    return render(request, 'core/contact.html')


def terms(request):
    return render(request, 'core/terms.html')

@require_http_methods(["GET"])
def get_weather(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    if not lat or not lon:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
    
    try:
        
        api_key = settings.WEATHER_API_KEY
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return JsonResponse({
                'temperature': round(data['main']['temp']),
                'location': data['name'],
                'description': data['weather'][0]['description']
            })
        else:
            return JsonResponse({'error': 'Weather data not available'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                NewsletterSubscription.objects.create(email=email)
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            except:
                messages.info(request, 'You are already subscribed to our newsletter.')
        else:
            messages.error(request, 'Please provide a valid email address.')
    return redirect('core:home#mcq-section') 