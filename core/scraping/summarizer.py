import json
from datetime import datetime, timedelta
from transformers import pipeline
import os

INPUT_JSON  = "./core/data/kathmandu_post_articles_by_category.json"
OUTPUT_JSON = "./core/data/yesterday_summaries.json"

# Function to split text into smaller chunks
def split_text(text, max_tokens=500):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Hierarchical summarization for long texts
def hierarchical_summarize(text, summarizer):
    chunks = split_text(text)
    intermediate_summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]
            intermediate_summaries.append(summary)
        except Exception as e:
            print(f"Failed to summarize chunk: {e}")
    combined_summary_text = " ".join(intermediate_summaries)
    try:
        final_summary = summarizer(combined_summary_text, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]
    except Exception as e:
        print(f"Final summarization failed: {e}")
        final_summary = combined_summary_text
    return final_summary

def main():
    print("Starting summarization...")

    # Load summarization pipeline here inside main to avoid global execution on import
    summarizer = pipeline(
        "summarization",
        model="philschmid/bart-large-cnn-samsum",
        tokenizer="philschmid/bart-large-cnn-samsum",
        device=0,  # Use CUDA if available, set -1 for CPU if needed
    )

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    print(f"Target dates: {yesterday} and {today}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        all_articles_by_category = json.load(f)

    summarized_by_category = {}

    for category, articles in all_articles_by_category.items():
        print(f"\nProcessing category: {category} ({len(articles)} articles)")
        summaries = []
        skipped = 0

        for art in articles:
            title = art.get("title", "No Title")
            url = art.get("url", "No URL")

            try:
                raw_date = art.get("date")
                article_date = datetime.fromisoformat(raw_date).date()
            except (ValueError, KeyError, TypeError) as e:
                print(f"Skipped due to invalid/missing date: {title} → {raw_date} | Error: {e}")
                skipped += 1
                continue

            if article_date not in (today, yesterday):
                skipped += 1
                continue

            body = art.get("body", "").strip()
            if not body:
                print(f"Skipped empty body: {title}")
                skipped += 1
                continue

            try:
                if len(body.split()) > 500:
                    summary = hierarchical_summarize(body, summarizer)
                else:
                    summary = summarizer(body, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]
            except Exception as e:
                print(f"Summarization failed for '{title}': {e}")
                skipped += 1
                continue

            summaries.append({
                "title": title,
                "summary": summary,
                "url": url,
                "date": str(article_date)
            })

        if summaries:
            summarized_by_category[category] = summaries
            print(f"{len(summaries)} summarized, {skipped} skipped.")
        else:
            print(f"No valid articles summarized in this category.")

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summarized_by_category, f, ensure_ascii=False, indent=2)

    print(f"\nTotal categories summarized: {len(summarized_by_category)} → Saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
