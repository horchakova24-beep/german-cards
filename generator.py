import os
import sys
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
    1. Используй исключительно естественную разговорную речь (Umgangssprache), которую используют носители прямо сейчас на улицах Германии в 2026 году.
    2. Избегай устаревших, чисто книжных, бумажных или официальных слов. Никакого старого стиля!
    3. Фразы должны быть полезными в реальной жизни.
    4. Для каждой фразы определи род главного немецкого существительного:
       - 'masc' если мужской (der)
       - 'fem' если женский (die)
       - 'neu' если средний (das)
       - 'other' если существительного нет, это множественное число или общее выражение.
    5. Пиши ответ максимально компактно, без лишних пробелов и ОБЯЗАТЕЛЬНО закрой квадратную скобку ']' в конце!
    
    Ответ выдай строго в формате JSON списка без объяснений и без ```json. 
    Пример:
    [{{"de": "Kann ich mit Karte zahlen?", "ru": "Могу я оплатить картой?", "gender": "fem"}},{{"de": "Der Kaffee ist echt lecker!", "ru": "Кофе очень вкусный!", "gender": "masc"}}]
    """

    # Склеиваем URL из частей, чтобы чат не вставил квадратные скобки!
    domain = "generativelanguage.googleapis.com"
    path = "/v1beta/models/gemini-flash-latest:generateContent?key="
    url = "https://" + domain + path + api_key

    headers = {"Content-Type": "application/json"}

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

            # Чистим ответ
            cleaned_text = ai_text.replace("```json", "").replace("```", "").strip()

            # --- УМНЫЙ АВТОРЕМОНТ JSON ---
            try:
                # Пробуем распарсить как есть
                new_words = json.loads(cleaned_text)
            except json.JSONDecodeError:
                print("Предупреждение: Получен поврежденный или оборванный JSON. Запуск авторемонта...")
                
                # Находим последнюю закрывающую фигурную скобку (конец целого объекта)
                last_brace = cleaned_text.rfind('}')
                if last_brace != -1:
                    # Обрезаем все до неё включительно и закрываем массив
                    repaired_text = cleaned_text[:last_brace + 1] + "]"
                    try:
                        new_words = json.loads(repaired_text)
                        print(f"Авторемонт успешен! Удалось спасти {len(new_words)} целых фраз из 25.")
                    except Exception as repair_error:
                        print(f"Критическая ошибка авторемонта: {repair_error}")
                        sys.exit(1)
                else:
                    print("Критическая ошибка: В ответе ИИ вообще нет валидных объектов JSON.")
                    sys.exit(1)

            print(f"Успешно обработано {len(new_words)} слов!")
            
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}")
        sys.exit(1)

    # --- ЗАПИСЬ В ОТДЕЛЬНЫЙ JSON ФАЙЛ ---
    try:
        os.makedirs("data", exist_ok=True)
        file_path = f"data/{topic}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(new_words, f, ensure_ascii=False, indent=4)
            
        print(f"Файл {file_path} успешно создан/обновлен новыми словами!")

    except Exception as e:
        print(f"Ошибка при сохранении JSON-файла: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_words()
