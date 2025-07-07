from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatHistory
from .utils import generate_chat_response, analyze_news, GeminiAIError, ContentModerationError
import json
import logging
import markdown

logger = logging.getLogger(__name__)

@login_required
def chat_interface(request):
    chat_history = ChatHistory.objects.filter(user=request.user).order_by('-created_at')[:20]  # limit for sidebar
    return render(request, 'ai_chat/chat_interface.html', {'chat_history': chat_history})

@csrf_exempt
@login_required
def chat_with_ai(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_type = data.get('type', 'chat')  # 'chat' or 'news'
            
            if message_type == 'news':
                return handle_news_analysis(request, data)
            else:
                return handle_chat_message(request, data)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in chat_with_ai: {str(e)}")
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Invalid request method',
        'success': False
    }, status=405)

def handle_news_analysis(request, data):
    """Handle news analysis requests"""
    news_title = data.get('news_title')
    news_body = data.get('news_body')
    analysis_type = data.get('analysis_type', 'comprehensive')
    
    if not news_title or not news_body:
        return JsonResponse({
            'error': 'News title and body are required',
            'success': False
        }, status=400)
    
    try:
        # Generate analysis using Gemini AI
        analysis = analyze_news(
            title=news_title,
            content=news_body,
            analysis_type=analysis_type
        )
        
        # Save chat history
        ChatHistory.objects.create(
            user=request.user,
            prompt=f"Analyze news ({analysis_type}): {news_title}",
            response=analysis['full_text'],
            news_title=news_title,
            metadata=json.dumps({
                'analysis_type': analysis_type,
                'timestamp': analysis['timestamp'],
                'sections': analysis['sections'],
                'formatted_html': analysis['formatted_html']
            })
        )
        
        return JsonResponse({
            'response': {
                'raw_text': analysis['full_text'],
                'formatted_html': analysis['formatted_html'],
                'sections': analysis['sections'],
                'analysis_type': analysis_type,
                'timestamp': analysis['timestamp']
            },
            'success': True
        })
        
    except GeminiAIError as e:
        logger.error(f"Gemini AI error: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def handle_chat_message(request, data):
    """Handle general chat messages"""
    message = data.get('message')
    stream = data.get('stream', False)
    
    if not message:
        return JsonResponse({
            'error': 'Message is required',
            'success': False
        }, status=400)
    
    try:
        # Get chat history for context
        history = get_chat_history_for_context(request.user)
        
        if stream:
            # Return streaming response
            return StreamingHttpResponse(
                stream_chat_response(message, history, request.user),
                content_type='text/event-stream'
            )
        
        # Generate normal response
        response_text = generate_chat_response(message, history)
        
        # Convert markdown to HTML
        formatted_html = markdown.markdown(response_text)
        
        # Save chat history
        ChatHistory.objects.create(
            user=request.user,
            prompt=message,
            response=response_text,
            metadata=json.dumps({
                'formatted_html': formatted_html
            })
        )
        
        return JsonResponse({
            'response': {
                'raw_text': response_text,
                'formatted_html': formatted_html
            },
            'success': True
        })
        
    except ContentModerationError as e:
        return JsonResponse({
            'error': 'Message failed content moderation',
            'success': False
        }, status=400)
    except GeminiAIError as e:
        logger.error(f"Gemini AI error: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def stream_chat_response(message, history, user):
    """Stream chat response chunks"""
    chunks = []
    try:
        # Initialize the response generator
        response_generator = generate_chat_response(message, history, stream=True)
        
        # Stream the response chunks
        for chunk in response_generator:
            if chunk:  # Only process non-empty chunks
                chunks.append(chunk)
                # Ensure proper JSON formatting
                data = json.dumps({'chunk': chunk})
                yield f"data: {data}\n\n"
        
        # If we have received any chunks, save the complete response
        if chunks:
            complete_response = ''.join(chunks)
            try:
                ChatHistory.objects.create(
                    user=user,
                    prompt=message,
                    response=complete_response
                )
            except Exception as e:
                logger.error(f"Error saving chat history: {str(e)}")
                # Don't raise the error, just log it
        else:
            # If no chunks were received, yield an error
            error_data = json.dumps({'error': 'No response generated'})
            yield f"data: {error_data}\n\n"
            return
            
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        error_data = json.dumps({'error': str(e)})
        yield f"data: {error_data}\n\n"
        return
    finally:
        # Always send the DONE signal
        yield "data: [DONE]\n\n"

def get_chat_history_for_context(user):
    """Get formatted chat history for AI context"""
    history = ChatHistory.objects.filter(user=user).order_by('-created_at')[:10]
    return [
        {
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': msg.prompt if i % 2 == 0 else msg.response
        }
        for i, msg in enumerate(reversed(history))
    ]

@login_required
def get_chat_history(request):
    chat_history = ChatHistory.objects.filter(user=request.user).values(
        'id', 'prompt', 'response', 'created_at', 'news_title', 'metadata'
    )
    return JsonResponse(list(chat_history), safe=False)

@login_required
def get_chat_by_id(request, chat_id):
    """Get specific chat history by ID"""
    try:
        chat = ChatHistory.objects.filter(user=request.user, id=chat_id).first()
        
        if not chat:
            logger.warning(f"Chat not found for ID: {chat_id}")
            return JsonResponse({
                'error': 'Chat not found',
                'success': False
            }, status=404)
            
        # Ensure metadata is properly formatted
        metadata = chat.metadata
        if metadata:
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata JSON for chat {chat_id}")
                    metadata = {}
            elif not isinstance(metadata, dict):
                logger.warning(f"Invalid metadata type for chat {chat_id}: {type(metadata)}")
                metadata = {}
        else:
            metadata = {}
        
        # Format the response
        chat_data = {
            'id': chat.id,
            'prompt': chat.prompt,
            'response': chat.response,
            'created_at': chat.created_at.isoformat(),
            'news_title': chat.news_title,
            'metadata': metadata
        }
        
        logger.info(f"Retrieved chat data for ID {chat_id}: {chat_data}")
            
        return JsonResponse({
            'chat': chat_data,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error fetching chat: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch chat history',
            'success': False
        }, status=500)
