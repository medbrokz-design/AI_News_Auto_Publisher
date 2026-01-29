import os
import asyncio
import feedparser
import google.generativeai as genai
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot

# Загрузка переменных окружения
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Источники RSS
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
]

def fetch_news():
    news_items = []
    yesterday = datetime.now() - timedelta(days=1)
    
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published_parsed = getattr(entry, 'published_parsed', None)
            if published_parsed:
                pub_date = datetime(*published_parsed[:6])
                if pub_date > yesterday:
                    news_items.append({
                        'title': entry.title,
                        'link': entry.link,
                        'summary': entry.summary if 'summary' in entry else ''
                    })
    return news_items

def summarize_news(news_list):
    if not news_list:
        return None

    text_to_process = ""
    for i, item in enumerate(news_list[:15], 1):
        text_to_process += f"Title: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"

    prompt = f"""
    Ты - AI-Orchestrator и Digital Entrepreneur. Твоя задача - превратить скучный список новостей в мощный дайджест для Telegram-канала "One News AI". Твоя аудитория - люди, которые хотят делать деньги и строить будущее с помощью ИИ.

    Используй следующий список новостей:
    {text_to_process}

    СТРУКТУРА ПОСТА (ИСПОЛЬЗУЙ ТОЛЬКО HTML):
    1. <b>Заголовок:</b> ⚡️ <b>ONE NEWS AI | ТВОЙ ПРЕДЕЛЬНЫЙ ДАЙДЖЕСТ</b>
    Добавь текущую дату и короткую, дерзкую фразу о состоянии рынка сегодня.

    2. <b>Новости (3-4 самых денежных или технологичных):</b>
       🔹 <a href="..."><b>ЗАГОЛОВОК НОВОСТИ</b></a>
       📝 <b>Суть:</b> Кратко, что произошло.
       💰 <b>Impact:</b> Как на этом заработать, сэкономить или какой бизнес запустить на этой базе. Будь прагматичен.
       ────────────────────

    3. <b>🛠 ИНСТРУМЕНТ / ПРОМПТ ДНЯ:</b>
       Найди среди новостей или предложи сам один конкретный ИИ-инструмент или "золотой промпт", который можно протестировать прямо сейчас. Опиши его ценность.

    4. <b>🎙 МНЕНИЕ ХАЙЗЕНБЕРГА:</b>
       Добавь 1-2 ироничных, глубоких или циничных предложения от лица "Доктора Хайзенберга" (твоего внутреннего AI-директора) по поводу сегодняшней повестки. Это должна быть "база", которая заставит задуматься.

    5. <b>Футер:</b> #AI #Money #Future #Automation

    ВАЖНО: 
    - НЕ ИСПОЛЬЗУЙ тег <br>. Используй обычные переносы строк.
    - Только разрешенные теги: <b>, <i>, <a>.
    - Будь острым на язык, избегай корпоративного булшита.
    """

    response = model.generate_content(prompt)
    return response.text

async def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Ошибка: TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не настроены в .env")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with bot:
        # Отключаем превью ссылок, чтобы пост был компактным
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=text, 
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        print("🚀 Сообщение успешно отправлено в Telegram!")

async def main():
    print("🔄 Сбор новостей...")
    items = fetch_news()
    print(f"✅ Найдено новостей: {len(items)}")
    
    if items:
        print("🤖 Gemini обрабатывает новости...")
        digest = summarize_news(items)
        
        if digest:
            print("\n--- ДАЙДЖЕСТ СФОРМИРОВАН ---\n")
            print(digest)
            
            # Сохраняем локально
            with open("D:\\Brain\\10_Projects\\AI_News_Auto_Publisher\\latest_digest.txt", "w", encoding="utf-8") as f:
                f.write(digest)
            
            # Отправляем в Telegram
            await send_to_telegram(digest)
        else:
            print("❌ Не удалось сгенерировать дайджест.")
    else:
        print("❌ Новых новостей за 24 часа нет.")

if __name__ == "__main__":
    asyncio.run(main())
