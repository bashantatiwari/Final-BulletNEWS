from shlex import quote
from django.shortcuts import render
import json
import os
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .models import GeneratedContent
from gtts import gTTS
import tempfile
import logging
from django.utils import timezone
from django.urls import reverse

logger = logging.getLogger(__name__)

def load_summaries():
    with open(os.path.join(settings.BASE_DIR, 'core', 'data', 'yesterday_summaries.json'), 'r') as f:
        return json.load(f)

@login_required
def myfeed_view(request):
    summaries = load_summaries()
    categories = list(summaries.keys())
    return render(request, 'newsfeed/feed.html', {
        'categories': categories,
        'summaries': summaries,
        'next': reverse('login')
    })

@login_required
@require_http_methods(["POST"])
def generate_pdf(request):
    category = request.POST.get('category')
    summaries = load_summaries()
    
    if category not in summaries:
        return JsonResponse({'error': 'Invalid category'}, status=400)
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"newsfeed_{category}_{timestamp}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'pdfs', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph(f"{category.title()} News Summary", title_style))
    story.append(Spacer(1, 20))
    
    # Add date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        spaceAfter=20
    )
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", date_style))
    story.append(Spacer(1, 20))
    
    # Add articles
    for article in summaries[category]:
        # Add article title
        story.append(Paragraph(article['title'], styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Add article summary
        story.append(Paragraph(article['summary'], styles['Normal']))
        
        # Add article date if available
        if 'date' in article:
            story.append(Paragraph(f"Published: {article['date']}", date_style))
        
        # Add article URL if available
        if 'url' in article:
            url_style = ParagraphStyle(
                'URLStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.blue,
                spaceAfter=20
            )
            story.append(Paragraph(f"Source: {article['url']}", url_style))
        
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    
    # Save record
    GeneratedContent.objects.create(
        user=request.user,
        content_type='PDF',
        category=category,
        file_path=filepath
    )
    
    return JsonResponse({'file_url': f'/media/pdfs/{filename}'})

@login_required
def download_content(request, content_id):
    try:
        content = GeneratedContent.objects.get(id=content_id, user=request.user)
        response = FileResponse(open(content.file_path, 'rb'))
        content.is_downloaded = True
        content.save()
        
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(content.file_path)}"'
            
        return response
    except GeneratedContent.DoesNotExist:
        return JsonResponse({'error': 'Content not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def generate_audio(request):
    try:
        category = request.POST.get('category')
        if not category:
            return JsonResponse({'error': 'Category is required'}, status=400)
            
        summaries = load_summaries()
        if category not in summaries:
            return JsonResponse({'error': f'Invalid category: {category}'}, status=400)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"newsfeed_{category}_{timestamp}.mp3"
        filepath = os.path.join(settings.MEDIA_ROOT, 'audio', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Prepare text for TTS
        text = f"News summary for {category.title()} category.\n\n"
        for article in summaries[category]:
            text += f"{article['title']}. {article['summary']}\n\n"
        
        # Generate audio file
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        
        # Verify file was created
        if not os.path.exists(filepath):
            return JsonResponse({'error': 'Failed to create audio file'}, status=500)
            
        # Save record
        GeneratedContent.objects.create(
            user=request.user,
            content_type='AUDIO',
            category=category,
            file_path=filepath
        )
        
        # Return JSON response with proper content type
        response = JsonResponse({
            'file_url': f'/media/audio/{filename}',
            'status': 'success'
        })
        response['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        print(f"Error generating audio: {str(e)}")  # For debugging
        response = JsonResponse({
            'error': f'Failed to generate audio: {str(e)}'
        }, status=500)
        response['Content-Type'] = 'application/json'
        return response

def audio_player(request, category):
    try:
        # Get the latest audio for this category
        latest_audio = GeneratedContent.objects.filter(
            category=category,
            content_type='audio'
        ).order_by('-generated_at').first()

        # If no recent audio exists, generate new
        if not latest_audio or (timezone.now() - latest_audio.generated_at).total_seconds() > 3600:
            summaries_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'yesterday_summaries.json')
            if not os.path.exists(summaries_path):
                return JsonResponse({'error': 'Summaries file not found'}, status=404)

            with open(summaries_path, 'r', encoding='utf-8') as f:
                summaries = json.load(f)

            if category not in summaries:
                return JsonResponse({'error': 'Invalid category'}, status=400)

            # Generate filename and path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'audio_{category}_{timestamp}.mp3'
            filepath = os.path.join(settings.MEDIA_ROOT, 'audio', filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Generate audio content
            text = f"Here are the latest news summaries for {category}:\n\n"
            for article in summaries[category]:
                text += f"{article['title']}. {article['summary']}\n\n"

            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filepath)

            # Save content to DB
            latest_audio = GeneratedContent.objects.create(
                user=request.user,
                content_type='AUDIO',
                category=category,
                file_path=filepath
            )

        # Build correct audio URL
        relative_path = os.path.relpath(latest_audio.file_path, settings.MEDIA_ROOT)
        encoded_path = quote(relative_path.replace('\\', '/'))  # Windows path fix
        audio_url = request.build_absolute_uri(settings.MEDIA_URL + encoded_path)

        return render(request, 'newsfeed/audio_player.html', {
            'category': category,
            'audio_url': audio_url
        })

    except Exception as e:
        print(f"Error in audio_player view: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)