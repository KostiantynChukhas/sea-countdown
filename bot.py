"""
Телеграм-бот «Сколько осталось до моря».

Режимы:
  python bot.py          — обновить закреплённое сообщение один раз и выйти
                           (для GitHub Actions / cron / любого планировщика)
  python bot.py --loop   — работать постоянно и обновлять каждые N секунд
                           (для своего сервера / GitHub Actions / Railway и т.п.)

Настройки берутся из переменных окружения (см. README.md):
  BOT_TOKEN   — токен бота от @BotFather (обязательно)
  CHAT_ID     — id группы, например -1001234567890 (обязательно)
  MESSAGE_ID  — id уже созданного сообщения (необязательно; если нет —
                бот сам отправит сообщение, закрепит его и запомнит id в state.json)
  TARGET      — дата поездки, по умолчанию 2026-11-17 07:00
  TZ_NAME     — часовой пояс, по умолчанию Europe/Kyiv
  INTERVAL    — пауза между обновлениями в секундах для --loop, по умолчанию 10
  MAX_RUN_SEC — через сколько секунд завершить --loop (для GitHub Actions), 0 = никогда
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo(os.environ.get("TZ_NAME", "Europe/Kyiv"))
TARGET = datetime.strptime(
    os.environ.get("TARGET", "2026-11-17 07:00"), "%Y-%m-%d %H:%M"
).replace(tzinfo=TZ)
INTERVAL_SEC = int(os.environ.get("INTERVAL", "10"))      # пауза между обновлениями в --loop, сек
MAX_RUN_SEC = int(os.environ.get("MAX_RUN_SEC", "0"))     # 0 = без ограничения; для GitHub Actions ~5.8 ч

STATE_FILE = Path(__file__).with_name("state.json")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method: str, **params):
    r = requests.post(f"{API}/{method}", json=params, timeout=30)
    data = r.json()
    if not data.get("ok"):
        # Telegram просит подождать — ждём и повторяем
        retry = (data.get("parameters") or {}).get("retry_after")
        if retry:
            time.sleep(int(retry) + 1)
            return tg(method, **params)
        raise RuntimeError(f"{method}: {data.get('description')}")
    return data["result"]


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def build_text(now: datetime) -> str:
    left = TARGET - now
    total_sec = int(left.total_seconds())
    date_str = TARGET.strftime("%d.%m.%Y о %H:%M")

    if total_sec <= 0:
        return (
            "🌊☀️ <b>МИ НА МОРІ!</b> ☀️🌊\n\n"
            "Зворотний відлік завершено. Усім гарного відпочинку! 🏖"
        )

    days, rem = divmod(total_sec, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"<b>{days}</b> {plural(days, 'день', 'дні', 'днів')}")
    if days or hours:
        parts.append(f"<b>{hours}</b> {plural(hours, 'година', 'години', 'годин')}")
    if days or hours or minutes:
        parts.append(f"<b>{minutes}</b> {plural(minutes, 'хвилина', 'хвилини', 'хвилин')}")
    parts.append(f"<b>{seconds}</b> {plural(seconds, 'секунда', 'секунди', 'секунд')}")

    # Полоска прогресса: 15 клеток, появляется за 30 дней (1 клетка = 2 дня)
    bar = ""
    if days <= 30:
        cells = 15
        filled = round((30 - days) / 30 * cells)
        bar = "\n\n" + "🟦" * filled + "⬜️" * (cells - filled)

    return (
        "🏖 <b>До моря залишилось</b>\n\n"
        "⏳ " + ", ".join(parts) + bar +
        f"\n\n📅 Виїзд: {date_str}\n"
        f"<i>оновлено {now.strftime('%d.%m %H:%M:%S')}</i>"
    )


def load_message_id():
    if os.environ.get("MESSAGE_ID"):
        return int(os.environ["MESSAGE_ID"])
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text()).get("message_id")
    return None


def save_message_id(message_id: int):
    STATE_FILE.write_text(json.dumps({"message_id": message_id}))


def update_once():
    now = datetime.now(TZ)
    text = build_text(now)
    message_id = load_message_id()

    if message_id is None:
        msg = tg("sendMessage", chat_id=CHAT_ID, text=text, parse_mode="HTML",
                 disable_notification=True)
        message_id = msg["message_id"]
        save_message_id(message_id)
        try:
            tg("pinChatMessage", chat_id=CHAT_ID, message_id=message_id,
               disable_notification=True)
        except RuntimeError as e:
            print(f"Не смог закрепить (нужны права админа): {e}")
        print(f"Создано сообщение, MESSAGE_ID = {message_id}")
        return

    try:
        tg("editMessageText", chat_id=CHAT_ID, message_id=message_id,
           text=text, parse_mode="HTML")
        print(f"Обновлено: {text.splitlines()[2]}", flush=True)
    except RuntimeError as e:
        # Текст не изменился — это не ошибка
        if "message is not modified" in str(e):
            print("Без изменений")
        else:
            raise


if __name__ == "__main__":
    if "--loop" in sys.argv:
        started = time.time()
        while True:
            try:
                update_once()
            except Exception as e:  # noqa: BLE001
                print("Ошибка:", e, flush=True)
            if MAX_RUN_SEC and time.time() - started > MAX_RUN_SEC:
                print("Лимит времени, завершаюсь (следующий запуск продолжит)", flush=True)
                break
            time.sleep(INTERVAL_SEC)
    else:
        update_once()
