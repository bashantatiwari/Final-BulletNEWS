import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------

BASE_URL = "https://kathmandupost.com"
OUTPUT_DIR = "./core/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "kathmandu_post_latest_updates.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

DELAY_BETWEEN_REQUESTS = 1.0

# ------------------ UTILITIES ------------------

def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def estimate_read_time(text: str, wpm: int = 200) -> int:
    words = len(text.split())
    return max(1, round(words / wpm))

def extract_date_from_url(url: str) -> datetime.date:
    match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day).date()
    return None

def get_original_image(proxy_url: str) -> str:
    try:
        parsed = urlparse(proxy_url)
        src_param = parse_qs(parsed.query).get("src")
        if src_param:
            return src_param[0]
    except Exception:
        pass
    return proxy_url

def extract_image(article) -> str:
    img_tag = article.find("img")
    if not img_tag:
        return None
    image_url = img_tag.get("data-src") or img_tag.get("src")
    if not image_url:
        return None
    return get_original_image(image_url)

# ------------------ SCRAPER ------------------

def scrape_latest_updates() -> list:
    print("Scraping latest updates...")
    url = BASE_URL
    soup = get_soup(url)
    articles = []

    # Get today's and yesterday's date
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)

    section = soup.find("div", class_="block--morenews")
    if not section:
        print(" No articles found in 'block--morenews'.")
        return []

    all_articles = section.find_all("article", class_="article-image")

    for i, article in enumerate(all_articles, 1):
        headline_tag = article.find("h3")
        link_tag = article.find("a", href=True)
        author_tag = article.find("span", class_="article-author")

        if not headline_tag or not link_tag:
            continue

        headline = headline_tag.get_text(strip=True)
        relative_link = link_tag["href"]
        full_link = urljoin(BASE_URL, relative_link)
        author = author_tag.get_text(strip=True).replace("By", "").strip() if author_tag else "Kathmandu Post"

        body = ""
        pub_date_str = "Unknown"
        pub_date_obj = None

        try:
            article_soup = get_soup(full_link)
            wrapper = article_soup.find("div", class_="subscribe--wrapperx")
            story = wrapper.find("section", class_="story-section") if wrapper else None
            paras = story.find_all("p") if story else []
            body = "\n\n".join(p.get_text(strip=True) for p in paras)

            # Extract date
            meta_date = article_soup.find("meta", property="article:published_time")
            if meta_date and meta_date.get("content"):
                pub_date_str = meta_date["content"][:10]
            else:
                time_tag = article_soup.find("time")
                if time_tag and time_tag.get("datetime"):
                    pub_date_str = time_tag["datetime"][:10]
                else:
                    extracted_date = extract_date_from_url(full_link)
                    if extracted_date:
                        pub_date_str = extracted_date.strftime("%Y-%m-%d")

            # Convert string to date object
            try:
                pub_date_obj = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            except:
                pub_date_obj = None

            # Skip articles that are not from today or yesterday
            if not pub_date_obj or pub_date_obj not in (today, yesterday):
                print(f"⏭Skipping outdated article: {headline} ({pub_date_str})")
                continue

        except Exception as e:
            print(f"Failed to fetch article content for {full_link}: {e}")
            continue

        read_time = f"{estimate_read_time(body)} min read" if body else "1 min read"
        image_url = extract_image(article)

        articles.append({
            "title": headline,
            "url": full_link,
            "author": f"By {author}",
            "read_time": read_time,
            "image_url": image_url,
            "body": body,
            "date": pub_date_str
        })

        print(f"  [{i}] {headline} ({pub_date_str})")
        time.sleep(DELAY_BETWEEN_REQUESTS)

    return articles

# ------------------ MAIN ------------------

def main():
    updates = scrape_latest_updates()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(updates, f, ensure_ascii=False, indent=2)
    print(f"\n Scraped {len(updates)} articles. Data saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
