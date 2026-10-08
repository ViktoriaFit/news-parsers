
import feedparser
import requests
import json
from datetime import datetime

# === ИСТОЧНИКИ НОВОСТЕЙ ===
SOURCES = [
    {"name": "Хабр", "url": "https://habr.com/ru/rss/all/all/"},
    {"name": "Tproger", "url": "https://tproger.ru/feed/"},
    {"name": "N+1", "url": "https://nplus1.ru/rss"},
    {"name": "Ведомости", "url": "https://www.vedomosti.ru/rss/news"},
    {"name": "Лента.ру", "url": "https://lenta.ru/rss/news"},
]

# === ФИЛЬТР: ключевые слова (только эти новости) ===
KEYWORDS = [
    "ai", "ии", "искусственный интеллект", "нейросет", "нейрон",
    "python", "программ", "код", "разработ", "ml", "модель"
]

# === КЛЮЧ GROQ ===
api_key = "gsk_ваш ключ"

# === ПРОКСИ ===
proxies = {
    "http": "http://127.0.0.1:12334",
    "https": "http://127.0.0.1:12334"
}

# === TELEGRAM (опционально) ===
TELEGRAM_BOT_TOKEN = ""  
TELEGRAM_CHAT_ID = ""    

# === 1. СОБИРАЕМ НОВОСТИ СО ВСЕХ ИСТОЧНИКОВ ===
print("Собираю новости...")
all_news = []

for source in SOURCES:
    try:
        print("Читаю:", source["name"])
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:10]:
            all_news.append({
                "source": source["name"],
                "title": entry.title,
                "link": entry.link
            })
    except Exception as e:
        print("Ошибка с", source["name"], ":", e)

print("Всего собрано:", len(all_news))

# === 2. ФИЛЬТРУЕМ ПО КЛЮЧЕВЫМ СЛОВАМ ===
filtered = []
for news in all_news:
    title_lower = news["title"].lower()
    for kw in KEYWORDS:
        if kw in title_lower:
            filtered.append(news)
            break

print("После фильтра:", len(filtered))
print()

if not filtered:
    print("Нет новостей по теме. Выхожу.")
    exit()

# === 3. СОХРАНЯЕМ В JSON ===
with open("news_list.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)
print("Сохранено в news_list.json")

# === 4. БЕРЁМ ПЕРВЫЕ 10 ДЛЯ РЕЗЮМЕ ===
titles = [n["title"] for n in filtered[:10]]
news_text = "\n".join("- " + t for t in titles)

print("\nНовости для резюме:")
for t in titles:
    print(" •", t)

# === 5. ОТПРАВЛЯЕМ В AI ===
prompt = (
    "Вот новости (отфильтрованы по теме AI и программирование):\n\n"
    + news_text
    + "\n\nСделай краткое резюме — о чём эти новости. "
    "3-5 предложений по-русски."
)

print("\nОтправляю в AI...")

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": prompt}]
        },
        proxies=proxies,
        timeout=60
    )
    data = response.json()

    if "choices" in data:
        summary = data["choices"][0]["message"]["content"]
        print("\n=== РЕЗЮМЕ ОТ AI ===")
        print(summary)

        # === 6. СОХРАНЯЕМ В ФАЙЛ ===
        with open("news_summary.txt", "w", encoding="utf-8") as f:
            f.write("РЕЗЮМЕ НОВОСТЕЙ\n")
            f.write("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")
            f.write("=" * 50 + "\n\n")
            f.write("ИСТОЧНИКИ: " + ", ".join(s["name"] for s in SOURCES) + "\n")
            f.write("НОВОСТЕЙ ОТОБРАНО: " + str(len(filtered)) + "\n\n")
            f.write("НОВОСТИ:\n")
            for i, t in enumerate(titles, 1):
                f.write(str(i) + ". " + t + "\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write("РЕЗЮМЕ:\n" + summary + "\n")

        print("\nСохранено в news_summary.txt")

        # === 7. ОТПРАВКА В TELEGRAM (если настроено) ===
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            tg_url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
            text = "📰 Новости за " + datetime.now().strftime("%d.%m") + ":\n\n" + summary
            try:
                requests.post(
                    tg_url,
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]},
                    proxies=proxies,
                    timeout=30
                )
                print("Отправлено в Telegram")
            except Exception as e:
                print("Ошибка Telegram:", e)
        else:
            print("(Telegram не настроен — пропущено)")

    else:
        print("Ошибка AI:", data)

except Exception as e:
    print("Ошибка:", e)
