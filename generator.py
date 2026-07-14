
import os
import sys
import re
import json
import urllib.request

def generate_words():
    # Получаем тему от робота-диспетчера
    topic = os.getenv("TOPIC", "restaurant")
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        print("Ошибка: API-ключ не найден. Пожалуйста, добавьте секретный ключ.")
        sys.exit(1)

    # Красивые названия тем для запроса к ИИ
    topic_translations = {
        "weather": "Погода и планы",
        "restaurant": "Кафе и ресторан",
        "city": "Ориентация в городе",
        "shopping": "Покупки и супермаркет",
        "health": "Самочувствие и врач",
        "hotel": "Поиск жилья / Отель",
        "job": "Работа и резюме",
        "hobby": "Хобби и свободное время",
        "guests": "В гостях / Праздники",
        "emergency": "Проблемы и ЧС"
    }
    
    topic_name_ru = topic_translations.get(topic, topic)

    print(f"Запуск генерации для темы: {topic_name_ru}...")

    # Инструкция для ИИ
    prompt = f"""
    Ты — молодой, дружелюбный и современный житель Германии в 2026 году. 
    Ты помогаешь составить учебные карточки для изучения живого, разговорного немецкого языка (Alltagssprache).
    
    Твоя задача — сгенерировать ровно 25 коротких, практичных фраз на тему: "{topic_name_ru}".
    
    СТРОГИЕ ПРАВИЛА:
    1. Используй исключительно естественную разговорную речь (Umgangssprache), которую используют носители прямо сейчас на улицах, в кафе или магазинах в 2026 году.
    2. Избегай устаревших, чисто книжных, бумажных или слишком официальных канцелярских оборотов (например, не пиши "Kaufmannsladen", пиши "Supermarkt"; не пиши "Mobiltelefon", пиши "Handy").
    3. Фразы должны быть полезными в реальной жизни.
    4. Для каждой фразы определи род главного немецкого существительного в предложении:
       - 'masc' если слово мужского рода (der)
       - 'fem' если женского (die)
       - 'neu' если среднего (das)
       - 'other' если существительного нет, оно во множественном числе или это общее выражение.
    
    Ответ выдай строго в формате JSON списка без лишнего текста, объяснений и markdown-разметки (без ```json). 
    Пример формата:
    [
      {{"de": "Kann ich mit Karte zahlen?", "ru": "Могу я оплатить картой?", "gender": "fem"}},
      {{"de": "Der Kaffee ist echt lecker!", "ru": "Кофе действительно очень вкусный!", "gender": "masc"}}
    ]
    """

    # Абсолютно чистая ссылка без скобок!
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
            new_words = json.loads(ai_text.strip())
            print(f"Успешно получено {len(new_words)} слов от ИИ!")
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}")
        sys.exit(1)

    # Встраиваем слова в наш index.html
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # Меняем содержимое внутри квадратных скобок [...] для выбранной темы
        pattern = rf'({topic}:\s*\[)(.*?)(\])'
        
        formatted_words = ",\n".join([f'                {{ de: "{w["de"]}", ru: "{w["ru"]}", gender: "{w["gender"]}" }}' for w in new_words])
        replacement = f"\\1\n{formatted_words}\n            \\3"

        new_html_content, n_subs = re.subn(pattern, replacement, html_content, count=1, flags=re.DOTALL)

        if n_subs == 0:
            print(f"⚠️ Внимание: тема '{topic}' не найдена в index.html или формат массива не совпал с шаблоном!")
            sys.exit(1)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_html_content)

        print("Файл index.html успешно обновлен новыми словами!")

    except Exception as e:
        print(f"Ошибка при обновлении index.html: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_words()
