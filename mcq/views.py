from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import MCQQuestion, MCQOption, MCQResponse
import random

# Create your views here.

@login_required
def mcq_view(request):
    # Get a random active question that the user hasn't answered
    answered_questions = MCQResponse.objects.filter(user=request.user).values_list('question_id', flat=True)
    available_questions = MCQQuestion.objects.filter(is_active=True).exclude(id__in=answered_questions)
    
    if not available_questions.exists():
        messages.info(request, "You've answered all available questions!")
        return render(request, 'mcq/no_questions.html')
    
    question = random.choice(list(available_questions))
    options = question.options.all()
    
    context = {
        'question': question,
        'options': options,
    }
    return render(request, 'mcq/mcq.html', context)

@login_required
def submit_response(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        option_id = request.POST.get('option_id')
        wants_another = request.POST.get('wants_another') == 'true'
        
        try:
            question = MCQQuestion.objects.get(id=question_id)
            selected_option = MCQOption.objects.get(id=option_id)
            
            # Check if the answer is correct
            is_correct = selected_option.is_correct
            
            # Save the response
            response = MCQResponse.objects.create(
                user=request.user,
                question=question,
                selected_option=selected_option,
                is_correct=is_correct,
                wants_another=wants_another
            )
            
            return JsonResponse({
                'success': True,
                'is_correct': is_correct,
                'correct_option': question.options.filter(is_correct=True).first().option_text if not is_correct else None
            })
            
        except (MCQQuestion.DoesNotExist, MCQOption.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid question or option'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })
