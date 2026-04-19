import os
import django

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generator.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
password = 'admin123'
email = 'admin@example.com'

try:
    # Пробуем найти пользователя
    user = User.objects.get(username=username)
    # Если есть — просто обновляем пароль и права
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    print(f"✅ User '{username}' updated!")
except User.DoesNotExist:
    # Если нет — создаем нового
    User.objects.create_superuser(username, email, password)
    print(f"✅ User '{username}' created!")