import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generator.settings')
django.setup()

from django.contrib.auth.models import User

username = 'root'
password = 'root123'
email = 'root@admin.com'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created with password '{password}'")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"✅ Password for '{username}' updated to '{password}'")