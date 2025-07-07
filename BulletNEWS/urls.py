"""
URL configuration for BulletNEWS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from users import views as user_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('news/', include('news.urls')),
    path('blog/', include('blog.urls')),
    path('newsfeed/', include('newsfeed.urls')),
    path('users/', include('users.urls')),
    path('login/', user_views.login_view, name='login'),
    path('register/', user_views.register, name='register'),
    path('logout/', user_views.logout_view, name='logout'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),      
    path('ai_chat/', include('ai_chat.urls')),
    path('mcq/', include('mcq.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
