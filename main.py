import json
import os
import random
import telebot
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from keep_alive import keep_alive  # для работы 24/7 на Replit

# === НАСТРОЙКИ ===
TOKEN = "ТВОЙ_ТОКЕН"  # вставь сюда токен своего бота
USERS_FILE = "data/users.json"
TIMEZONE = pytz.timezone("Asia/Makassar")  # Бали

bot = telebot.TeleBot(TOKEN)

# === ФРАЗЫ ===
morning_smile_phrases = [
    "Доброе утро! ☀ Не забудь улыбнуться.😊",
    "Проснулся? Улыбка – лучший старт дня! 😁",
    "Улыбнись новому дню! 🌞",
    "Начни утро с улыбки! 🌼"
]

evening_questions = [
    "Что тебе сегодня снилось? 🌙",
    "Какое у тебя было намерение сегодня?",
    "Что хорошего произошло за день?",
    "Опиши своё состояние одним словом."
]

# === ФУНКЦИИ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ===
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# === ОТПРАВКА СООБЩЕНИЙ ===
def send_morning_questions():
    users = load_users()
    for chat_id in users:
        bot.send_message(chat_id, random.choice(morning_smile_phrases))
        users[chat_id]["last_activity"] = datetime.now(TIMEZONE).isoformat()
    save_users(users)
    print("✅ Утренние вопросы отправлены")

def send_evening_questions():
    users = load_users()
    for chat_id in users:
        for q in evening_questions:
            bot.send_message(chat_id, q)
        users[chat_id]["last_activity"] = datetime.now(TIMEZONE).isoformat()
    save_users(users)
    print("🌙 Вечерние вопросы отправлены")

# === ОБРАБОТКА СООБЩЕНИЙ ===
@bot.message_handler(content_types=['text', 'voice'])
def handle_message(message):
    users = load_users()
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {"message_count": 0, "last_activity": None}

    users[chat_id]["message_count"] += 1
    users[chat_id]["last_activity"] = datetime.now(TIMEZONE).isoformat()
    save_users(users)

    bot.send_message(chat_id, "Записал ✍️")

# === ПЛАНИРОВЩИК ===
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(send_morning_questions, 'cron', hour=8, minute=0)
scheduler.add_job(send_evening_questions, 'cron', hour=22, minute=0)
scheduler.start()

# === ЗАПУСК ===
if __name__ == "__main__":
    keep_alive()  # запускаем веб-сервер для пингов

    # планировщик (часовой пояс у тебя Asia/Makassar)
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_morning_questions, 'cron', hour=8,  minute=0)
    scheduler.add_job(send_evening_questions, 'cron', hour=22, minute=0)
    scheduler.start()

    print("✅ Bot is running…")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    
    