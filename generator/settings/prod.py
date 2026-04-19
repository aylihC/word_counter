from .base import *
import os
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['*']

# Подключаем PostgreSQL из переменной окружения
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'), ssl_require=True)
}