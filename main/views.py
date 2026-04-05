from django.shortcuts import render
import re
from collections import Counter

def counter(request):
    if request.method == 'POST':
        text = request.POST['texttocount']

        if text != '':
            text_clean = re.sub(r'\.(?=[A-ZА-ЯЁ])', ' ', text)
            words = [w for w in text_clean.split() if re.search(r'[a-zA-Zа-яА-ЯёЁ]', w)]
            word = len(words)
            chars = len(text)
            word_label = 'word' if word == 1 else 'words'
            i = True

            # Топ 5 самых частых слов
            top_words = Counter(words).most_common(5)

            return render(request, 'counter.html', {
                'word': word,
                'word_label': word_label,
                'chars': chars,
                'text': text,
                'i': i,
                'on': 'active',
                'top_words': top_words,
            })

        else:
            return render(request, 'counter.html', {'on': 'active'})

    else:
        return render(request, 'counter.html', {'om': 'active'}) 