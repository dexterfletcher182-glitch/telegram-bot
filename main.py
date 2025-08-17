import os, json, random
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import telebot

# ==== НАСТРОЙКИ ====
TZ = pytz.timezone("Asia/Makassar")  # Бали
USERS_FILE = "data/users.json"
TOKEN = os.getenv("BOT_TOKEN", "").strip()  # ЗАДАЙ В РЕНДЕРЕ как переменную окружения
if not TOKEN:
    raise RuntimeError("Отсутствует BOT_TOKEN в переменных окружения.")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ==== ТЕКСТЫ ====
morning_openers = [
    "Доброе утро! ☀️ Не забудь улыбнуться 🙂",
    "Проснулся? Улыбка — лучший старт дня! 😁",
    "Улыбнись новому дню! 🌞",
    "Начнём мягко. Сделай вдох-выдох и улыбнись 🌼"
]

# Утро: база — СНЫ + лёгкое намерение + одно слово-состояние
morning_questions = [
    "Что тебе снилось? Если помнишь — запиши 📝",
    "Какое мягкое намерение на сегодня? (одно простое действие, настроение или фокус)",
    "Опиши своё состояние одним словом."
]

# Вечер: подведение итогов
evening_questions = [
    "Что получилось сегодня?",
    "Что было сложным (и как ты с этим справился)?",
    "Чему ты рад сегодня?"
]

# ==== ХРАНИЛКА ПОЛЬЗОВАТЕЛЕЙ ====
def _ensure_store():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_users():
    _ensure_store()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    _ensure_store()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== РАССЫЛКИ ====
def send_morning():
    users = load_users()
    now = datetime.now(TZ).isoformat()
    for chat_id in list(users.keys()):
        try:
            bot.send_message(chat_id, random.choice(morning_openers))
            for q in morning_questions:
                bot.send_message(chat_id, q)
            users[chat_id]["last_activity"] = now
        except Exception as e:
            # если бот заблокирован (403), пользователь недоступен — удалим
            if getattr(e, "error_code", None) == 403:
                users.pop(chat_id, None)
            else:
                print(f"[morning] error for {chat_id}: {e}")
    save_users(users)
    print("✅ Morning broadcast done")

def send_evening():
    users = load_users()
    now = datetime.now(TZ).isoformat()
    for chat_id in list(users.keys()):
        try:
            bot.send_message(chat_id, "Хочешь подвести итоги дня? 🌙")
            for q in evening_questions:
                bot.send_message(chat_id, q)
            users[chat_id]["last_activity"] = now
        except Exception as e:
            if getattr(e, "error_code", None) == 403:
                users.pop(chat_id, None)
            else:
                print(f"[evening] error for {chat_id}: {e}")
    save_users(users)
    print("🌙 Evening broadcast done")

# ==== КОМАНДЫ ====
@bot.message_handler(commands=["start"])
def cmd_start(m):
    users = load_users()
    cid = str(m.chat.id)
    users.setdefault(cid, {"subscribed_at": datetime.now(TZ).isoformat(), "last_activity": None})
    save_users(users)
    bot.reply_to(m,
        "Привет! Я *inside* — твой тихий друг.\n"
        "Утром в *08:00* и вечером в *22:00* по Бали я пришлю тебе короткие вопросы.\n\n"
        "Команды:\n"
        "• /test_morning — прислать утренние вопросы сейчас\n"
        "• /test_evening — прислать вечерние вопросы сейчас\n"
        "• /stop — остановить напоминания"
    )

@bot.message_handler(commands=["stop"])
def cmd_stop(m):
    users = load_users()
    cid = str(m.chat.id)
    if cid in users:
        users.pop(cid)
        save_users(users)
        bot.reply_to(m, "Отключил напоминания. Если захочешь вернуться — напиши /start.")
    else:
        bot.reply_to(m, "Ты и так не был подписан 🙂")

@bot.message_handler(commands=["test_morning"])
def cmd_test_morning(m):
    cid = str(m.chat.id)
    bot.send_message(cid, random.choice(morning_openers))
    for q in morning_questions:
        bot.send_message(cid, q)

@bot.message_handler(commands=["test_evening"])
def cmd_test_evening(m):
    cid = str(m.chat.id)
    bot.send_message(cid, "Хочешь подвести итоги дня? 🌙")
    for q in evening_questions:
        bot.send_message(cid, q)

# Любой текст/аудио — подтверждаем
@bot.message_handler(content_types=["text", "voice"])
def any_msg(m):
    # тут можно писать в файл потом; для MVP просто подтверждаем
    bot.reply_to(m, "Записал ✍️")

# ==== ПЛАНИРОВЩИК ====
scheduler = BackgroundScheduler(timezone=TZ)
scheduler.add_job(send_morning, "cron", hour=8, minute=0)
scheduler.add_job(send_evening, "cron", hour=22, minute=0)
scheduler.start()

if __name__ == "__main__":
    print("✅ inside-bot running (polling)…")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)