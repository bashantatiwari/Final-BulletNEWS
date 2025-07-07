import google.generativeai as genai
from django.conf import settings
import logging
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, List, Dict, Generator, Union
import concurrent.futures
import markdown
import re

logger = logging.getLogger(__name__)

# Model configurations
MODELS = {
    'chat': "gemini-2.0-flash",
    'analysis': "gemini-2.0-flash",
}

# Rate limiting settings
MAX_RETRIES = 2
RETRY_DELAY = 20  # seconds
REQUEST_WINDOW = 60  # seconds
MAX_REQUESTS_PER_MINUTE = 10

# Chat configurations
MAX_HISTORY_LENGTH = 10
MAX_MESSAGE_LENGTH = 4096

# Custom Exceptions
class GeminiAIError(Exception):
    """Custom exception for Gemini AI errors."""
    pass

class MessageTooLongError(GeminiAIError):
    """Raised when message exceeds maximum length."""
    pass

class ContentModerationError(GeminiAIError):
    """Raised when content violates moderation policies."""
    pass

# Rate limiter class
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

    def can_make_request(self) -> bool:
        now = datetime.now()
        self.requests = [r for r in self.requests if now - r < timedelta(seconds=self.window_seconds)]
        return len(self.requests) < self.max_requests

    def add_request(self):
        self.requests.append(datetime.now())

# Rate limiter instances
chat_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE, REQUEST_WINDOW)
analysis_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE * 2, REQUEST_WINDOW)

# Rate-limiting decorator
def rate_limited(limiter):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(MAX_RETRIES):
                if limiter.can_make_request():
                    limiter.add_request()
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if "quota" in str(e).lower() and attempt < MAX_RETRIES - 1:
                            logger.warning(f"Rate limit hit, retrying in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                            continue
                        raise
                else:
                    logger.warning(f"Rate limit enforced, waiting {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
            raise GeminiAIError("Max retries exceeded while respecting rate limits")
        return wrapper
    return decorator

# Model cache
model_cache = {}

def initialize_gemini(model_type: str = 'chat') -> genai.GenerativeModel:
    if model_type in model_cache:
        return model_cache[model_type]

    if not settings.GEMINI_API_KEY:
        raise GeminiAIError("GEMINI_API_KEY is not set in environment variables")
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(MODELS[model_type])
        model_cache[model_type] = model
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        raise GeminiAIError(f"Failed to initialize Gemini model: {e}")

def moderate_content(text: str) -> bool:
    forbidden_words = ['inappropriate', 'offensive', 'harmful']
    return not any(word in text.lower() for word in forbidden_words)

def truncate_history(history: List[Dict[str, str]], max_length: int = MAX_HISTORY_LENGTH) -> List[Dict[str, str]]:
    return history[-max_length:] if len(history) > max_length else history

def format_message(message: str) -> str:
    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        raise MessageTooLongError(f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters")
    return message

def with_timeout(func, *args, timeout=10, **kwargs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        return future.result(timeout=timeout)

def preprocess_markdown(text: str) -> str:
    text = text.replace('•', '-').replace('–', '-')
    text = '\n'.join(line.strip() for line in text.strip().splitlines())
    return text

def markdown_to_html(md_text: str) -> str:
    cleaned = preprocess_markdown(md_text)
    return markdown.markdown(cleaned, extensions=['extra'])

def validate_markdown(text: str) -> bool:
    """
    Validate that the Markdown text contains basic structural elements (e.g., headers, lists).
    Returns True if valid, False otherwise.
    """
    if not text.strip():
        return False
    has_header = bool(re.search(r'^#{1,6}\s+.+$', text, re.MULTILINE))
    has_list = bool(re.search(r'^- .+$', text, re.MULTILINE))
    return has_header or has_list

def clean_malformed_markdown(md_text: str) -> str:
    lines = md_text.split('\n')
    cleaned_lines = []
    buffer = ""
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            cleaned_lines.append(stripped)
            continue

        if in_code_block:
            cleaned_lines.append(line)
            continue

        if not stripped:
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ""
            cleaned_lines.append("")
            continue

        # Fix malformed headers (e.g., "#Header" -> "# Header")
        if re.match(r'^#{1,6}\w', stripped):
            stripped = re.sub(r'^(#{1,6})(\w)', r'\1 \2', stripped)

        # Standardize bullets to "- "
        if re.match(r'^[-*•]\s*', stripped):
            stripped = re.sub(r'^[-*•]\s*', '- ', stripped)
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ""
            cleaned_lines.append(stripped)
        elif re.match(r'^\d+\.\s*', stripped):
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ""
            cleaned_lines.append(stripped)
        else:
            buffer += " " + stripped

    if buffer:
        cleaned_lines.append(buffer.strip())

    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text.strip()

@rate_limited(chat_limiter)
def generate_chat_response(
    message: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    stream: bool = False
) -> Union[str, Generator[str, None, None]]:
    try:
        message = format_message(message)
        if not moderate_content(message):
            raise ContentModerationError("Message failed content moderation")

        model = initialize_gemini('chat')

        instructions = """
Please format the response using **Markdown**, strictly following these rules:

1. Use **bold** for key terms or section headers.
2. Use `-` for bullet points with a space after the dash.
3. Do not use asterisks (`*`) or other symbols for bullets or styling.
4. Add exactly one blank line between paragraphs or lists.
5. Avoid excessive spacing or inconsistent formatting.
6. Each bullet must be on its own line.
7. Keep the structure clean and minimal.
8. Do not include unclosed tags or malformed Markdown.

Example:

A **tree** is a perennial plant.

- Has a single stem or trunk
- Supports branches and leaves
- Essential to the ecosystem

User message:
""" + message

        if chat_history:
            chat_history = truncate_history(chat_history)
            chat = model.start_chat(history=[{"role": msg["role"], "parts": [msg["content"]]} for msg in chat_history])
            response = chat.send_message(instructions, stream=stream)
        else:
            response = model.generate_content(instructions, stream=stream)

        if stream:
            def response_generator():
                buffer = ""
                try:
                    for chunk in response:
                        if chunk.text:
                            buffer += chunk.text
                            # Only yield when buffer contains a complete Markdown structure
                            if re.search(r'\n\n|\n$|^#{1,6}\s|- ', buffer, re.MULTILINE):
                                cleaned = clean_malformed_markdown(buffer)
                                if cleaned and validate_markdown(cleaned):
                                    yield markdown_to_html(cleaned)
                                else:
                                    logger.warning(f"Invalid Markdown in chunk: {cleaned[:200]}")
                                buffer = ""
                    # Yield any remaining buffer
                    if buffer:
                        cleaned = clean_malformed_markdown(buffer)
                        if cleaned and validate_markdown(cleaned):
                            yield markdown_to_html(cleaned)
                        else:
                            logger.warning(f"Invalid Markdown in final buffer: {cleaned[:200]}")
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield "Error: Message generation interrupted."
            return response_generator()
        else:
            if not response or not response.text:
                raise GeminiAIError("Empty response from Gemini AI")
            fixed_response = clean_malformed_markdown(response.text.strip())
            if not validate_markdown(fixed_response):
                logger.warning(f"Response does not meet Markdown formatting standards: {fixed_response[:200]}")
                fixed_response = "## Response\n" + fixed_response
            return markdown_to_html(fixed_response)

    except Exception as e:
        logger.error(f"Chat generation error: {e}")
        raise GeminiAIError(f"Failed to generate chat response: {e}")

@rate_limited(analysis_limiter)
def analyze_news(
    title: str,
    content: str,
    analysis_type: str = 'comprehensive'
) -> Dict[str, str]:
    try:
        model = initialize_gemini('analysis')

        analysis_prompts = {
            'quick': """
Provide a brief summary of this news article in Nepali using markdown:

## सारांश
- मुख्य बुँदा १
- मुख्य बुँदा २
""",
            'comprehensive': """
Analyze this news in Nepali using markdown formatting:

## सारांश
[२-३ वाक्य सारांश]

## मुख्य बुँदाहरू
- मुख्य घटनाहरू वा तथ्यहरूको बुलेट लिस्ट

## प्रभाव विश्लेषण
[परिणामहरूको व्याख्या]

## पृष्ठभूमि
[सम्बन्धित ऐतिहासिक/प्रासंगिक विवरणहरू]

## सम्बन्धित विषयहरू
- सम्बन्धित विषयहरूको बुलेट लिस्ट

## विशेषज्ञहरूको राय
[यदि कुनै छ भने विशेषज्ञहरूको विचारहरू समावेश गर्नुहोस्]

## अतिरिक्त अन्तर्दृष्टिहरू
[अन्य टिप्पणीहरू]
""",
            'technical': """
Provide a technical analysis in Nepali using markdown:

## प्राविधिक विवरणहरू
[समावेश प्रविधिको व्याख्या]

## बजार प्रभाव
[अर्थतन्त्र वा क्षेत्रमा प्रभाव]

## जोखिम र न्यूनीकरण
[सम्भावित जोखिमहरूको सूची]

## सिफारिसहरू
[व्यावहारिक वा प्राविधिक सल्लाहहरू]
"""
        }

        prompt = f"""
### Article Title:
{title}

### Content:
{content}

{analysis_prompts.get(analysis_type, analysis_prompts['comprehensive'])}

Ensure the response is clean, structured, and uses markdown best practices.
Strictly follow these Markdown rules:
1. Use **bold** for key terms or section headers.
2. Use `-` for bullet points with a space after the dash.
3. Do not use asterisks (`*`) or other symbols for bullets or styling.
4. Add exactly one blank line between paragraphs or lists.
5. Avoid excessive spacing or inconsistent formatting.
6. Each bullet must be on its own line.
7. Keep the structure clean and minimal.
8. Do not include unclosed tags or malformed Markdown.
9. Write all content in Nepali language.
"""

        response = with_timeout(model.generate_content, prompt, timeout=100)

        if not response or not response.text:
            raise GeminiAIError("Empty response from Gemini AI")

        analysis_text = preprocess_markdown(response.text)
        cleaned_text = clean_malformed_markdown(analysis_text)

        # Validate expected sections
        expected_sections = {
            'quick': ['सारांश'],
            'comprehensive': ['सारांश', 'मुख्य बुँदाहरू', 'प्रभाव विश्लेषण', 'पृष्ठभूमि', 'सम्बन्धित विषयहरू', 'विशेषज्ञहरूको राय', 'अतिरिक्त अन्तर्दृष्टिहरू'],
            'technical': ['प्राविधिक विवरणहरू', 'बजार प्रभाव', 'जोखिम र न्यूनीकरण', 'सिफारिसहरू']
        }.get(analysis_type, ['सारांश'])

        if not validate_markdown(cleaned_text):
            logger.warning(f"Analysis response does not meet Markdown standards: {cleaned_text[:200]}")
            cleaned_text = "## सारांश\nकुनै वैध विश्लेषण उपलब्ध छैन।"

        sections = cleaned_text.split('\n\n')
        section_headers = [re.match(r'^##\s*(.+)', s) for s in sections]
        section_headers = [m.group(1) for m in section_headers if m]

        # Ensure all expected sections are present
        for header in expected_sections:
            if header not in section_headers:
                logger.warning(f"Missing expected section '{header}' in analysis response")
                sections.append(f"## {header}\nकुनै जानकारी उपलब्ध छैन।")

        return {
            'title': title,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'sections': sections,
            'full_text': cleaned_text,
            'formatted_html': markdown_to_html(cleaned_text)
        }

    except Exception as e:
        logger.error(f"News analysis error: {e}")
        raise GeminiAIError(f"Failed to analyze news: {e}")

def is_gemini_working() -> bool:
    results = {}

    for model_type, model_name in MODELS.items():
        try:
            model = initialize_gemini(model_type)
            response = model.generate_content("Test message")
            results[model_type] = bool(response and response.text)
        except Exception as e:
            logger.error(f"Health check failed for {model_type}: {e}")
            results[model_type] = False

    return any(results.values())