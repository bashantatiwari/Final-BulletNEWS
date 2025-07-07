import os
import django
from dotenv import load_dotenv
import logging
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BulletNEWS.settings')
django.setup()

from ai_chat.utils import initialize_gemini, GeminiAIError

def test_gemini():
    print("\nTesting Gemini AI configuration...")
    
    # Test environment variables
    from django.conf import settings
    print("\nEnvironment Information:")
    print(f"GEMINI_API_KEY exists: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    if settings.GEMINI_API_KEY:
        print(f"GEMINI_API_KEY length: {len(settings.GEMINI_API_KEY)}")
        print(f"GEMINI_API_KEY format check: {'AI' in settings.GEMINI_API_KEY}")
    
    # List available models
    print("\nAvailable Models:")
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        for m in genai.list_models():
            print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")
        logger.error("Error listing models:", exc_info=True)
    
    # Test Gemini initialization
    print("\nTesting Gemini Initialization:")
    try:
        model = initialize_gemini()
        print("✅ Successfully initialized Gemini model")
        
        # Test basic generation
        print("\nTesting Content Generation:")
        try:
            response = model.generate_content("Hello, are you working?")
            if response and response.text:
                print("✅ Successfully generated test content")
                print("-" * 50)
                print("Response:", response.text.strip())
                print("-" * 50)
            else:
                print("❌ Empty response from Gemini AI")
        except Exception as e:
            print(f"❌ Error generating content: {str(e)}")
            logger.error(f"Content generation error details:", exc_info=True)
            
    except GeminiAIError as e:
        print(f"❌ Gemini initialization error: {str(e)}")
        logger.error("Initialization error details:", exc_info=True)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        logger.error("Unexpected error details:", exc_info=True)

if __name__ == '__main__':
    test_gemini() 