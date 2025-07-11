from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-secret-key-for-dev')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'final-bulletnews.onrender.com').split(',')

# External API Keys (fallback for local testing)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'dummy-api-key')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'dummy-weather-key')

# Raise error only in production
if not DEBUG and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Social Auth
SOCIAL_AUTH_LOGIN_ERROR_URL = 'failure'
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'newsfeed:myfeed'
LOGOUT_REDIRECT_URL = 'users:login'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'newsfeed:myfeed'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_RECEIVER_EMAIL = 'tiwarieshant033@gmail.com'

# Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local Apps
    'users.apps.UsersConfig',
    'blog',
    'news',
    'core',
    'newsfeed',
    'ai_chat',
    'mcq',

    # Third-party
    'social_django',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'BulletNEWS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'BulletNEWS.wsgi.application'

# DATABASES — fallback to SQLite when DATABASE_URL is not provided
default_db = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
DATABASES = {
    'default': dj_database_url.parse(
        default_db,
        conn_max_age=600,
        ssl_require=default_db.startswith("postgres") and not DEBUG
    )
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary Media Storage Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Media URL (kept for admin preview and compatibility)
MEDIA_URL = '/media/'

# Create media subfolders only in local dev
if DEBUG:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_SUBDIRS = ['pdfs', 'audio']
    for subdir in MEDIA_SUBDIRS:
        os.makedirs(os.path.join(MEDIA_ROOT, subdir), exist_ok=True)

# Default Primary Key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
