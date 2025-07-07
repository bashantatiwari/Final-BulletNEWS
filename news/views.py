
import json, os
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def news_list(request):
    # File paths
    category_json_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'kathmandu_post_articles_by_category.json')
    latest_json_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'kathmandu_post_latest_updates.json')

    # Load category articles
    with open(category_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load latest headlines separately
    # Load latest headlines separately
    with open(latest_json_path, 'r', encoding='utf-8') as f:
        latest_data = json.load(f)

# Since the file is a list of articles, use it directly
    latest_headlines = latest_data


    # Define categories with icons
    categories = [
        {"name": "Politics", "icon": "fa-landmark"},
        {"name": "Money", "icon": "fa-coins"},
        {"name": "Health", "icon": "fa-heartbeat"},
        {"name": "Sports", "icon": "fa-football-ball"},
        {"name": "Climate Environment", "icon": "fa-tree"},
        {"name": "Science Technology", "icon": "fa-flask"},
    ]

    # Organize articles by category
    category_news_dict = {}
    featured_news_dict = {}

    for cat in categories:
        key = cat["name"].lower().replace(" ", "-")  # keys in JSON like 'science-technology'
        articles = data.get(key, [])
        category_news_dict[cat["name"]] = articles
        featured_news_dict[cat["name"]] = articles[0] if articles else None

    # Use the loaded latest updates directly
    

    # Pick first article for featured (fallback)
    featured = None
    for articles in featured_news_dict.values():
        if articles:
            featured = articles
            break

    return render(request, "news/news_list.html", {
        "categories": categories,
        "category_news_dict": category_news_dict,
        "featured_news_dict": featured_news_dict,
        "latest_headlines": latest_headlines,
        "featured": featured,
    })



def news_detail(request, category, article_index):
    if category == 'latest':
        # Load from latest updates JSON
        json_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'kathmandu_post_latest_updates.json')
    else:
        # Load from category-based JSON
        json_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'kathmandu_post_articles_by_category.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # For 'latest', data is a list
        if category == 'latest':
            articles = data  # expecting a list
        else:
            articles = data.get(category, [])  # expecting a dict of lists

        # Get article by index
        if 0 <= article_index < len(articles):
            article = articles[article_index]
        else:
            return render(request, "404.html", status=404)

        return render(request, "news/news_detail.html", {"article": article})

    except FileNotFoundError:
        return render(request, "404.html", status=404)

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'profile.html', context)

