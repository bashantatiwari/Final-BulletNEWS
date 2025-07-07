from django.urls import path
from . import views

app_name = 'mcq'

urlpatterns = [
    path('', views.mcq_view, name='mcq'),
    path('submit/', views.submit_response, name='submit_response'),
] 