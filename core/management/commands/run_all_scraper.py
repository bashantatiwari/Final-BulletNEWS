from django.core.management.base import BaseCommand
import os
import sys

# Optional: Fix import issues if running from different context
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../.."))
sys.path.append(BASE_DIR)

# Import your script's main functions
try:
    from core.scraping.scraper import main as scrape_by_category
    from core.scraping.scrapLatestUpdates import main as scrape_latest
    from core.scraping.summarizer import main as summarize_news
except ImportError as e:
    print(f"⚠️ Import failed: {e}")
    sys.exit(1)

class Command(BaseCommand):
    help = 'Run all scraping and summarization scripts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(' Running all scrapers and summarizer...'))

        try:
            self.stdout.write("1️ Running category-based scraper...")
            scrape_by_category()
        except Exception as e:
            self.stderr.write(f" Error running category scraper: {e}")

        try:
            self.stdout.write("2️ Running latest news scraper...")
            scrape_latest()
        except Exception as e:
            self.stderr.write(f" Error running latest scraper: {e}")

        try:
            self.stdout.write("3️ Running summarization script...")
            summarize_news()
        except Exception as e:
            self.stderr.write(f" Error running summarizer: {e}")

        self.stdout.write(self.style.SUCCESS(' All tasks completed.'))
