import os
from datetime import datetime

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .bot import router, build_message, load_schedule

# === Переменные окружения ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
TOPIC_ID = int(os.environ.get("TOPIC_ID", "0")) or None
CRON_SECRET = os.environ.get("CRON_SECRET", "")

# === Инициализация бота и диспетчера ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(router)

app = FastAPI()


@app.post("/api/bot")
async def telegram_webhook(request: Request):
    """Принимает обновления от Telegram."""
    update = await request.json()
    await dp.feed_raw_update(bot, update)
    return Response(status_code=200)


@app.get("/api/cron")
async def cron_send_schedule(request: Request):
    """Вызывается Vercel Cron Job. Отправляет расписание в чат."""
    # Проверка секрета (защита от посторонних вызовов)
    if CRON_SECRET:
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {CRON_SECRET}":
            return Response(status_code=401, content="Unauthorized")

    data = load_schedule()
    today = datetime.now().date()
    text = build_message(data, today)

    kwargs = {"chat_id": CHAT_ID, "text": text}
    if TOPIC_ID:
        kwargs["message_thread_id"] = TOPIC_ID

    await bot.send_message(**kwargs)
    await bot.session.close()
    return {"ok": True, "sent_to": CHAT_ID}