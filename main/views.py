from django.shortcuts import render
import re
from collections import Counter

def counter(request):
    if request.method == 'POST':
        text = request.POST['texttocount']

        if text != '':
            text_clean = re.sub(r'\.(?=[A-ZА-ЯЁ])', ' ', text)
            words = [w for w in text_clean.split() if w.strip()]
            word = len(words)
            chars = len(text)
            word_label = 'word' if word == 1 else 'words'
            i = True

            # Топ 5 самых частых слов
            words_lower = [w.lower() for w in words]
            top_words = sorted(Counter(words_lower).most_common(5), key=lambda x: (-x[1], x[0]))

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