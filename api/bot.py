import json
from datetime import datetime, date, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

WEEKDAYS_RU = {
    0: "Понедельник", 1: "Вторник", 2: "Среда",
    3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье",
}

# Путь к файлу относительно корня проекта
BASE_DIR = Path(__file__).parent.parent
SCHEDULE_FILE = BASE_DIR / "schedule.json"

router = Router()


def load_schedule() -> dict:
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_lessons_for_date(data: dict, target: date) -> list[dict]:
    target_iso = target.isoformat()
    lessons = [item for item in data["schedule"] if target_iso in item.get("dates", [])]
    lessons.sort(key=lambda x: int(x["pair"].split("-")[0]))
    return lessons


def find_next_day_with_lessons(data: dict, start: date, max_days: int = 60):
    for i in range(1, max_days + 1):
        candidate = start + timedelta(days=i)
        lessons = get_lessons_for_date(data, candidate)
        if lessons:
            return candidate, lessons
    return None, []


def format_lesson(lesson: dict, idx: int | None = None) -> str:
    prefix = f"{idx}. " if idx is not None else "• "
    return (
        f"{prefix}<b>{lesson['subject']}</b>\n\n"
        f"   🕒 {lesson['pair']} пара | {lesson['time']}\n\n"
        f"   👤 {lesson['teacher']}\n\n"
        f"   🚪 ауд. {lesson['room']}"
    )


def format_day_header(d: date) -> str:
    return f"{WEEKDAYS_RU[d.weekday()]}, {d.strftime('%d.%m.%Y')}"


def build_message(data: dict, today: date) -> str:
    today_lessons = get_lessons_for_date(data, today)
    parts = [f"📅 <b>Расписание на {format_day_header(today)}</b>\n"]

    if today_lessons:
        parts.append(f"🎓 <b>Сегодня {len(today_lessons)} пар(ы):</b>\n")
        for i, lesson in enumerate(today_lessons, start=1):
            parts.append(format_lesson(lesson, idx=i))
            parts.append("")
    else:
        parts.append("😴 <b>Сегодня пар нет.</b>\n")

    next_day, next_lessons = find_next_day_with_lessons(data, today)
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    if next_day:
        parts.append("\n🔜 <b>Ближайший день с парами:</b>")
        parts.append(f"<b>{format_day_header(next_day)}</b>\n")
        for i, lesson in enumerate(next_lessons, start=1):
            parts.append(format_lesson(lesson, idx=i))
            parts.append("")
    else:
        parts.append("\n🔜 В ближайшие 2 месяца пар не найдено.")

    return "\n".join(parts).strip()


@router.message(lambda m: m.text == "/today")
async def cmd_today(message: Message):
    data = load_schedule()
    today = datetime.now().date()
    await message.answer(build_message(data, today))