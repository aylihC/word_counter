from django.shortcuts import render
import re
from collections import Counter
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.shortcuts import redirect
import csv
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from .models import LoginAttempt
from django_ratelimit.decorators import ratelimit


@ratelimit(key='ip', rate='10/m', block=True)
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        ip = request.META.get('REMOTE_ADDR')

        attempt, created = LoginAttempt.objects.get_or_create(ip=ip)

        if attempt.blocked_until and attempt.blocked_until > timezone.now():
            return render(request, 'login.html', {
                'error': 'Too many failed attempts. Try again in 5 minutes.'
            })

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            attempt.attempts += 1
            if attempt.attempts >= 3:
                attempt.blocked_until = timezone.now() + timedelta(minutes=5)
            attempt.save()
            remaining = max(0, 3 - attempt.attempts)
            return render(request, 'login.html', {'error': f'User not found. {remaining} attempts remaining.'})

        user = authenticate(request, username=username, password=password)
        if user:
            attempt.attempts = 0
            attempt.blocked_until = None
            attempt.save()
            login(request, user)
            return redirect('/')
        else:
            attempt.attempts += 1
            if attempt.attempts >= 3:
                attempt.blocked_until = timezone.now() + timedelta(minutes=5)
            attempt.save()
            remaining = max(0, 3 - attempt.attempts)
            return render(request, 'login.html', {'error': f'Wrong password. {remaining} attempts remaining.'})

    return render(request, 'login.html')





def counter(request):
    if request.method == 'POST':
        text = request.POST['texttocount']

        if text != '':
            text_clean = re.sub(r'\.(?=[A-ZА-ЯЁ])', ' ', text)
            words = [w for w in text_clean.split() if w.strip()]
    
            ignore_numbers = request.POST.get('ignore_numbers') == '1'
            if ignore_numbers:
                words = [w for w in words if not re.match(r'^\d+$', w)]
    
            word = len(words)
            chars = len(text.strip())
            chars_no_spaces = len(text.strip().replace(' ', '').replace('\n', '').replace('\r', ''))
            word_label = 'word' if word == 1 else 'words'
            i = True

            # Топ 5 самых частых слов
            case_sensitive = request.POST.get('case_sensitive') == '1'

            if case_sensitive:
                words_counted = words
            else:
                words_counted = [w.lower() for w in words]

            top_words = sorted(Counter(words_counted).most_common(5), key=lambda x: (-x[1], x[0]))


            if request.user.is_authenticated:
                from .models import SearchHistory
                SearchHistory.objects.create(
                    user=request.user,
                    text=text,
                    word_count=word,
                    char_count=chars
                )



            return render(request, 'counter.html', {
                'word': word,
                'word_label': word_label,
                'chars': chars,
                'chars_no_spaces': chars_no_spaces,
                'text': text,
                'i': i,
                'on': 'active',
                'top_words': top_words,
                'case_sensitive': case_sensitive,
                'ignore_numbers': ignore_numbers,
            })

        else:
            return render(request, 'counter.html', {'on': 'active'})

    else:
        return render(request, 'counter.html', {'om': 'active'}) 
    

def export_txt(request):
    if request.method == 'POST':
        text = request.POST.get('text', '')
        word = request.POST.get('word', '')
        chars = request.POST.get('chars', '')
        chars_no_spaces = request.POST.get('chars_no_spaces', '')

        content = f"""Word Counter Results
====================
Text:
{text}

====================
Words: {word}
Characters: {chars}
Characters without spaces: {chars_no_spaces}
"""
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="word_counter_result.txt"'
        return response    
    

@ratelimit(key='ip', rate='5/m', block=True)
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        print(f"DEBUG USERNAME: '{username}'")
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if password1 != password2:
            return render(request, 'register.html', {'error': 'Passwords do not match'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already taken'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered'})
        
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = request.get_host()
        activation_link = f'http://{domain}/activate/{uid}/{token}/'

        send_mail(
            'Activate your account',
            f'Hi {username}! Click the link to activate your account:\n\n{activation_link}',
            None,
            [email],
        )    

        return render(request, 'register.html', {'success': 'Check your email to activate your account!'})
    

    return render(request, 'register.html')



def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        ip = request.META.get('REMOTE_ADDR')

        attempt, created = LoginAttempt.objects.get_or_create(ip=ip)

        # Проверяем блокировку
        if attempt.blocked_until and attempt.blocked_until > timezone.now():
            return render(request, 'login.html', {
                'error': 'Too many failed attempts. Try again in 5 minutes.'
            })

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            attempt.attempts += 1
            if attempt.attempts >= 3:
                attempt.blocked_until = timezone.now() + timedelta(minutes=5)
            attempt.save()
            remaining = max(0, 3 - attempt.attempts)
            return render(request, 'login.html', {'error': f'User not found. {remaining} attempts remaining.'})

        user = authenticate(request, username=username, password=password)
        if user:
            attempt.attempts = 0
            attempt.blocked_until = None
            attempt.save()
            login(request, user)
            return redirect('/')
        else:
            attempt.attempts += 1
            if attempt.attempts >= 3:
                attempt.blocked_until = timezone.now() + timedelta(minutes=5)
            attempt.save()
            remaining = max(0, 3 - attempt.attempts)
            return render(request, 'login.html', {'error': f'Wrong password. {remaining} attempts remaining.'})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')    



@staff_member_required
def export_emails(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Date Joined', 'Last Login'])
    
    users = User.objects.filter(is_active=True).order_by('-date_joined')
    for user in users:
        writer.writerow([user.username, user.email, user.date_joined, user.last_login])
    
    return response



def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('/')
    else:
        return render(request, 'register.html', {'error': 'Activation link is invalid or expired'})