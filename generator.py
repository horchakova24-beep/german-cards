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

    # Инструкция для ИИ: требуем живой, современный язык 2026 года и компактный JSON
    prompt = f"""
    Ты — молодой, дружелюбный и современный житель Германии в 2026 году. 
    Ты помогаешь составить учебные карточки для изучения живого, разговорного немецкого языка (Alltagssprache).
    
    Твоя задача — сгенерировать ровно 25 коротких, практичных фраз на тему: "{topic_name_ru}".
    
    СТРОГИЕ ПРАВИЛА:
    1. Используй исключительно естественную разговорную речь (Umgangssprache), которую используют носители прямо сейчас на улицах Германии в 2026 году.
    2. Избегай устаревших, чисто книжных, бумажных или официальных слов (например, не пиши "Kaufmannsladen", пиши "Supermarkt"; не пиши "Mobiltelefon", пиши "Handy"). Никакого старого стиля!
    3. Фразы должны быть полезными в реальной жизни.
    4. Для каждой фразы определи род главного немецкого существительного:
       - 'masc' если мужской (der)
       - 'fem' если женский (die)
       - 'neu' если средний (das)
       - 'other' если существительного нет, это множественное число или общее выражение.
    5. Пиши ответ максимально компактно, без лишних пробелов, не трать токены, чтобы JSON не обрезался в конце, и ОБЯЗАТЕЛЬНО закрой квадратную скобку ']' в конце!
    
    Ответ выдай строго в формате JSON списка без объяснений и без ```json. 
    Пример:
    [{{"de": "Kann ich mit Karte zahlen?", "ru": "Могу я оплатить картой?", "gender": "fem"}},{{"de": "Der Kaffee ist echt lecker!", "ru": "Кофе очень вкусный!", "gender": "masc"}}]
    """

    # Чистый рабочий URL
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=){api_key}"

    headers = {"Content-Type": "application/json"}
    
    # Настройки: отключаем размышления и даем большой лимит на вывод
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 8192,
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Чистим ответ на всякий случай
            cleaned_text = ai_text.replace("```json", "").replace("```", "").strip()
            
            # Проверяем, закрыт ли JSON массив
            if not cleaned_text.endswith("]"):
                cleaned_text += "]"
                
            new_words = json.loads(cleaned_text)
            print(f"Успешно получено {len(new_words)} слов от ИИ!")
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}")
        print(f"--- Сырой ответ ИИ (для отладки) ---")
        try:
            print(ai_text)
        except:
            pass
        sys.exit(1)

    # Встраиваем слова в index.html
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

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
