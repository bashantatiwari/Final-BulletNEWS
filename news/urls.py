from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('news/<str:category>/<int:article_index>/', views.news_detail, name='news_detail'),
    path('profile/', views.profile, name='profile'),
]
