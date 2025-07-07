from django.urls import path
from . import views

app_name = 'ai_chat'
 
urlpatterns = [
    path('chat/', views.chat_interface, name='chat_interface'),
    path('api/chat/', views.chat_with_ai, name='chat_with_ai'),
    path('api/history/', views.get_chat_history, name='get_chat_history'),
    path('api/chat/<int:chat_id>/', views.get_chat_by_id, name='get_chat_by_id'),
] 