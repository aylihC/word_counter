from .base import *
import os
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['*']

# Настройка базы данных
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'), ssl_require=True)
}

# Настройки для Render (HTTPS и CSRF)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://word-counter-rn8r.onrender.com'] 
