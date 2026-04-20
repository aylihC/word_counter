from django.shortcuts import render
import re
import os
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
from textblob import TextBlob
from pypdf import PdfReader
from fpdf import FPDF
from datetime import datetime


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
        # 📁 Обработка загруженного файла
        uploaded_file = request.FILES.get('text_file')
        text = ''

        if uploaded_file:
            file_name = uploaded_file.name.lower()

            # Проверяем тип файла
            if file_name.endswith('.txt'):
                # TXT файл
                try:
                    text = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    text = uploaded_file.read().decode('latin-1')

            elif file_name.endswith('.pdf'):
                # PDF файл
                try:
                    reader = PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        extracted_text = page.extract_text()
                        if extracted_text:
                            text += extracted_text + "\n"
                except Exception as e:
                # Если PDF не читается (защищен паролем или поврежден)
                    context = {
                        'error': 'Не удалось прочитать PDF файл. Убедитесь, что он не защищен паролем.'
                    }
                    return render(request, 'counter.html', context)
            else:
            # Неподдерживаемый формат
                context = {
                    'error': 'Поддерживаются только .txt и .pdf файлы.'
                }
                return render(request, 'counter.html', context)
        else:
        # Если файла нет, берём текст из поля ввода
            text = request.POST.get('texttocount', '')


        if text.strip():
            # 1️⃣ Заменяем знаки препинания (кроме точки) на пробелы, чтобы разделять слова
            # ! ? , ; : ( ) [ ] { } - — – теперь работают как разделители
            text_clean = re.sub(r'[!?,;:()\[\]{}\-—–]', ' ', text)

            # 2️⃣ Твоя оригинальная логика для точки:
            # Разделяем только если после точки идет ЗАГЛАВНАЯ буква
            text_clean = re.sub(r'\.(?=[A-ZА-ЯЁ])', ' ', text_clean)

            # 3️⃣ Разбиваем текст на список слов
            words = text_clean.split()

            # 4️⃣ Убираем оставшуюся пунктуацию по краям слов (например, точку в конце "dasas.")
            words = [re.sub(r'^[^\w]+|[^\w]+$', '', w) for w in words]
            words = [w for w in words if w]  # Удаляем пустые строки

            # 5️⃣ Игнорирование чисел
            ignore_numbers = request.POST.get('ignore_numbers') == '1'
            if ignore_numbers:
                words = [w for w in words if not re.match(r'^\d+$', w)]

            # 6️⃣ Регистр
            case_sensitive = request.POST.get('case_sensitive') == '1'
            if not case_sensitive:
                words = [w.lower() for w in words]

            # 7️⃣ Стоп-слова (фильтруем только для аналитики)
            stop_words = {
                'и', 'в', 'на', 'не', 'о', 'по', 'с', 'у', 'до', 'от', 'за', 'под', 'над',
                'а', 'но', 'или', 'как', 'что', 'это', 'так', 'же', 'ли', 'бы',
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need'
            }
            filtered_words = [w for w in words if w.lower() not in stop_words]

            # 8️⃣ Базовая статистика
            total_words = len(words)
            unique_words = len(set(filtered_words))
            chars = len(text.strip())
            chars_no_spaces = len(text.replace(' ', '').replace('\n', '').replace('\r', ''))
            word_label = 'word' if total_words == 1 else 'words'

            # 9️⃣ Топ слов с процентами и правильным склонением time/times
            word_freq = Counter(filtered_words)
            top_words_data = []
            for w, count in word_freq.most_common(10):
                percent = round((count / total_words * 100), 1) if total_words > 0 else 0
                # ✅ Исправление грамматики
                time_label = '1 time' if count == 1 else f'{count} times'
                top_words_data.append({
                    'word': w,
                    'count': count,
                    'percent': percent,
                    'time_label': time_label
                })

             # --- ⏱️ Расчет времени чтения ---
            WPM_READ = 200  # Слов в минуту для чтения
            WPM_SPEAK = 130 # Слов в минуту для речи


             # Расчет минут и секунд
            def format_time(word_count, wpm):
                if word_count == 0:
                    return "0 sec"
                total_minutes = word_count / wpm
                minutes = int(total_minutes)
                seconds = int((total_minutes - minutes) * 60)
                
                if minutes > 0:
                    return f"{minutes} min {seconds} sec"
                else:
                    return f"~{seconds} sec"
                
            reading_time = format_time(total_words, WPM_READ)
            speaking_time = format_time(total_words, WPM_SPEAK)
            # ---------------------------------    

            # --- 🤖 AI Анализ настроения ---
            try:
                # Создаем объект TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # От -1 (негатив) до 1 (позитив)
                subjectivity = blob.sentiment.subjectivity  # От 0 (факт) до 1 (мнение)

                # Определяем настроение
                if polarity > 0.1:
                    sentiment_label = "Positive 😊"
                    sentiment_color = "#10b981"  # Зеленый
                elif polarity < -0.1:
                    sentiment_label = "Negative 😔"
                    sentiment_color = "#ef4444"  # Красный
                else:
                    sentiment_label = "Neutral 😐"
                    sentiment_color = "#f59e0b"  # Желтый

                # Процент субъективности
                subjectivity_percent = round(subjectivity * 100)

            except Exception as e:
                # Если ошибка (например, текст не на английском)
                sentiment_label = "N/A"
                sentiment_color = "#6b7280"
                subjectivity_percent = 0
            # ------------------------------    


            # 💾 Сохранение в историю
            if request.user.is_authenticated:
                from .models import SearchHistory
                SearchHistory.objects.create(
                    user=request.user,
                    text=text,
                    word_count=total_words,
                    char_count=chars
                )

            return render(request, 'counter.html', {
                'word': total_words,
                'word_label': word_label,
                'chars': chars,
                'chars_no_spaces': chars_no_spaces,
                'unique_words': unique_words,
                'text': text,
                'top_words': top_words_data,
                'case_sensitive': case_sensitive,
                'ignore_numbers': ignore_numbers,
                'reading_time': reading_time,
                'speaking_time': speaking_time,
                'sentiment_label': sentiment_label,
                'sentiment_color': sentiment_color,
                'subjectivity_percent': subjectivity_percent,
            })
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