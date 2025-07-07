import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
from urllib.parse import urljoin
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------

BASE_URL = "https://kathmandupost.com"
OUTPUT_DIR = "./core/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "kathmandu_post_articles_by_category.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

CATEGORIES = [
    "politics",
    "money",
    "health",
    "sports",
    "climate-environment",
    "science-technology"
]

MAX_PAGES_PER_CATEGORY = 3
DELAY_BETWEEN_REQUESTS = 1.0

# ------------------ UTILITIES ------------------

def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_date_from_url(url: str) -> datetime.date:
    match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day).date()
    return datetime.min.date()

def estimate_read_time(text: str, wpm: int = 200) -> int:
    words = len(text.split())
    return max(1, round(words / wpm))

# ------------------ SCRAPERS ------------------

def scrape_category_links(category: str, max_pages: int) -> set:
    print(f"📂 Scraping category: {category}")
    article_links = set()
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=30)

    for page in range(1, max_pages + 1):
        page_url = f"{BASE_URL}/{category}?page={page}"
        print(f"  🔗 Page {page}: {page_url}")
        try:
            soup = get_soup(page_url)
            anchors = soup.find_all("a", href=True)

            for a in anchors:
                href = a["href"]
                if re.match(rf"^/{category}/\d{{4}}/\d{{2}}/\d{{2}}/", href):
                    full_url = urljoin(BASE_URL, href)
                    article_date = extract_date_from_url(full_url)

                    if cutoff_date <= article_date <= today:
                        article_links.add(full_url)
                    else:
                        print(f"    ⏩ Skipped old article: {full_url}")

            time.sleep(DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            print(f"  ⚠️ Failed to fetch page {page}: {e}")
            continue

    return article_links

def scrape_article(url: str) -> dict:
    try:
        soup = get_soup(url)

        # Title
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"].strip() if og_title and og_title.get("content") else "No title"

        # Body
        wrapper = soup.find("div", class_="subscribe--wrapperx")
        story = wrapper.find("section", class_="story-section") if wrapper else None
        paras = story.find_all("p") if story else []
        body = "\n\n".join(p.get_text(strip=True) for p in paras)

        # Date
        pub_date = extract_date_from_url(url)

        author = "By Kathmandu Post"  # Default author

        # Image URL
        og_image = soup.find("meta", property="og:image")
        image_url = og_image["content"].strip() if og_image and og_image.get("content") else None

        # Read time calculation (1 min per ~200 words)
        word_count = len(body.split())
        read_time = f"{max(1, word_count // 200)} min read"

        return {
            "url": url,
            "title": title,
            "body": body,
            "date": pub_date.strftime("%Y-%m-%d"),  # Only date, no time
            "author": author,
            "image_url": image_url,
            "read_time": read_time
        }

    except Exception as e:
        print(f"    ⚠️ Failed to scrape article: {e}")
        return None

# ------------------ MAIN ------------------

def main():
    all_articles = {}

    for category in CATEGORIES:
        urls = scrape_category_links(category, MAX_PAGES_PER_CATEGORY)
        articles = []

        for i, url in enumerate(urls, 1):
            print(f"    📄 [{i}/{len(urls)}] Fetching article: {url}")
            article = scrape_article(url)
            if article:
                articles.append(article)
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # Sort articles by date (most recent first)
        articles.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
        all_articles[category] = articles

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Scraping complete! Data saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
