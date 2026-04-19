import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generator.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
password = 'admin123'
email = 'admin@example.com'

# Удаляем старого admin если есть
User.objects.filter(username=username).delete()

# Создаем нового
user = User.objects.create_superuser(username, email, password)
user.is_active = True
user.save()

print(f"✅ User '{username}' created with password '{password}'")