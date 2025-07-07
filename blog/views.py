from django.shortcuts import render, get_object_or_404
from .models import BlogPost

def blog_list(request):
    posts = BlogPost.objects.all()
    return render(request, 'blog/blog_list.html', {'posts': posts})

def blog_detail(request, id):
    post = get_object_or_404(BlogPost, id=id)
    return render(request, 'blog/blog_detail.html', {'post': post})
