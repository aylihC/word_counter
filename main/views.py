from django.shortcuts import render
import re
from collections import Counter
from django.http import HttpResponse

def counter(request):
    if request.method == 'POST':
        text = request.POST['texttocount']

        if text != '':
            text_clean = re.sub(r'\.(?=[A-ZА-ЯЁ])', ' ', text)
            words = [w for w in text_clean.split() if w.strip()]
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