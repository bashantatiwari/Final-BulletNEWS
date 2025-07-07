from django.urls import path
from . import views

app_name = 'newsfeed'

urlpatterns = [
    path('', views.myfeed_view, name='myfeed'),
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
    path('generate-audio/', views.generate_audio, name='generate_audio'),
    path('audio-player/<str:category>/', views.audio_player, name='audio_player'),
    path('download/<int:content_id>/', views.download_content, name='download_content'),
] 