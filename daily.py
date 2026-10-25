"""Щоденний пост: скільки днів залишилось до моря + приємний слоган."""

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo(os.environ.get("TZ_NAME", "Europe/Kyiv"))
TARGET = datetime.strptime(
    os.environ.get("TARGET", "2026-11-17 07:00"), "%Y-%m-%d %H:%M"
).replace(tzinfo=TZ)

SLOGANS = [
    "Море вже чекає на нас і тихенько шепоче хвилями 🌊",
    "Ще трохи — і пісок між пальцями замість будильника ☀️",
    "Кожен день наближає нас до сонця, солі та свободи 🐚",
    "Пакуй настрій — валізу спакуємо пізніше 🧳",
    "Скоро будемо засинати під шум прибою 🌙",
    "Море не питає, як минув тиждень. Воно просто лікує 💙",
    "Сонцезахисний крем уже мріє про нашу шкіру 🧴",
    "Думки вже на пляжі, тіло скоро наздожене 🏖",
    "Найкращий антистрес — горизонт, де небо зустрічає воду 🌅",
    "Ще кілька днів — і жодних дедлайнів, лише хвилі 🌊",
    "Чайки вже репетирують привітальну пісню для нас 🕊",
    "Солоний вітер вже десь пише наші імена 💨",
    "Тримаємось! Попереду коктейлі, захід сонця і море ❤️",
    "Відпустка — це коли найважче рішення: плавати чи засмагати 😎",
    "Посміхайся — море ближче, ніж учора 😊",
    "Скоро замість новин — тільки шум хвиль і крики чайок 🐦",
    "Ми вже майже чуємо запах моря та свіжої кукурудзи 🌽",
    "Рахуємо дні, як мушлі на березі 🐚",
    "Ще трохи терпіння — і перше пірнання наше! 🤿",
    "Сонце вже заряджає промені спеціально для нас ☀️",
    "Попереду теплий пісок, холодні напої і гарячі засмаги 🍹",
    "Мрії про море сьогодні стали ще на день реальнішими ✨",
    "Хвилі вже вишикувались у чергу, щоб нас обійняти 🌊",
    "Запасаймося усмішками — на морі вони знадобляться 😄",
    "Ще один день до найкращих фото цього року 📸",
]


def plural(n, one, few, many):
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def build_text(now):
    days = (TARGET.date() - now.date()).days
    if days < 0:
        return None
    if days == 0:
        return "🌊☀️ <b>СЬОГОДНІ ЇДЕМО НА МОРЕ!</b> ☀️🌊\n\nГарного відпочинку всім! 🏖"
    if days == 1:
        head = "🔥 <b>Завтра — море!</b>"
    else:
        head = f"🏖 До моря залишилось <b>{days}</b> {plural(days, 'день', 'дні', 'днів')}"
    return f"{head}\n\n{SLOGANS[days % len(SLOGANS)]}\n\n📅 Виїзд: {TARGET.strftime('%d.%m.%Y о %H:%M')}"


if __name__ == "__main__":
    text = os.environ.get("CUSTOM_TEXT") or build_text(datetime.now(TZ))
    if text is None:
        print("Поїздка вже минула")
    else:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=30,
        )
        r.raise_for_status()
        print(text)
