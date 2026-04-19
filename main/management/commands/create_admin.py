from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create admin user if not exists'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin123'
        email = 'admin@example.com'

        # Если пользователь уже есть — НИЧЕГО НЕ ДЕЛАЕМ с паролем
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'️ User {username} already exists. Skipping.'))
        else:
            # Если нет — создаем
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'✅ User {username} created with password {password}'))