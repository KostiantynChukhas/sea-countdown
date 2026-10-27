"""Щоденний смішний пост на реальних даних: погода в Києві vs Шарм-ель-Шейх."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo(os.environ.get("TZ_NAME", "Europe/Kyiv"))
TARGET = datetime.strptime(
    os.environ.get("TARGET", "2026-11-17 07:00"), "%Y-%m-%d %H:%M"
).replace(tzinfo=TZ)

KYIV = (50.45, 30.52)
SHARM = (27.915, 34.33)


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
    "Рахуємо дні, як мушлі на березі 🐚",
    "Ще трохи терпіння — і перше пірнання наше! 🤿",
    "Сонце вже заряджає промені спеціально для нас ☀️",
    "Попереду теплий пісок, холодні напої і гарячі засмаги 🍹",
    "Мрії про море сьогодні стали ще на день реальнішими ✨",
    "Хвилі вже вишикувались у чергу, щоб нас обійняти 🌊",
    "Запасаймося усмішками — на морі вони знадобляться 😄",
    "Ще один день до найкращих фото цього року 📸",
    "Рибки-клоуни вже готують виставу біля рифу 🐠",
]


def plural(n, one, few, many):
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def weather(lat, lon):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "timezone": "auto",
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,sunshine_duration,sunset",
                "forecast_days": 1},
        timeout=30,
    ).json()
    return r["current"], {k: v[0] for k, v in r["daily"].items()}


def sea_temp(lat, lon):
    try:
        r = requests.get(
            "https://marine-api.open-meteo.com/v1/marine",
            params={"latitude": lat, "longitude": lon, "timezone": "auto",
                    "current": "sea_surface_temperature,wave_height"},
            timeout=30,
        ).json()["current"]
        return r.get("sea_surface_temperature"), r.get("wave_height")
    except Exception:  # noqa: BLE001
        return None, None


def kyiv_mood(code, t):
    if code >= 71 and code <= 86:
        return "сніг ❄️ — ідеальний час дістати пляжні шльопанці й подивитись на них з любов'ю"
    if code >= 51:
        return "дощ ☔️ — тренуємось бути мокрими, на морі знадобиться"
    if code >= 45:
        return "туман 🌫 — навіть місто не бачить сенсу без моря"
    if code >= 3:
        return "сіро й хмарно ☁️ — небо явно сумує за нами заздалегідь"
    if t < 5:
        return "сонячно, але холодно 🥶 — сонце світить, але не гріє, як колишній"
    return "навіть сонечко ☀️, але це лише розминка"


def sea_joke(sst):
    if sst is None:
        return "Море за прогнозом — тепле й чекає 🌊"
    if sst >= 27:
        return f"Вода в морі <b>{sst:.0f}°</b> — це як ванна, тільки з рибками 🐠"
    if sst >= 25:
        return f"Вода в морі <b>{sst:.0f}°</b> — заходиш і не верещиш, перевірено 🐠"
    return f"Вода в морі <b>{sst:.0f}°</b> — бадьоро, як ранкова кава 🐠"


def build_text(now):
    days = (TARGET.date() - now.date()).days
    if days < 0:
        return None
    if days == 0:
        return "🌊☀️ <b>СЬОГОДНІ ЛЕТИМО В ШАРМ!</b> ☀️🌊\n\nКуртки — в шафу, крем — у кишеню! 🏖"

    kc, kd = weather(*KYIV)
    sc, sd = weather(*SHARM)
    sst, wave = sea_temp(*SHARM)
    kt, st = kc["temperature_2m"], sc["temperature_2m"]
    diff = st - kt
    sun_h = sd["sunshine_duration"] / 3600 if sd.get("sunshine_duration") else None
    sunset = sd["sunset"][-5:] if sd.get("sunset") else None

    if days == 1:
        head = "🔥 <b>Завтра — Шарм-ель-Шейх!</b>"
    else:
        head = f"🏖 До моря залишилось <b>{days}</b> {plural(days, 'день', 'дні', 'днів')}"

    lines = [
        head,
        "",
        f"📡 <b>Звіт з двох фронтів:</b>",
        f"🇺🇦 Київ: <b>{kt:.0f}°</b> — {kyiv_mood(kc['weather_code'], kt)}",
        f"🇪🇬 Шарм: <b>{st:.0f}°</b> (до {sd['temperature_2m_max']:.0f}° вдень) — люди там зараз страждають від вибору лежака 😎",
        "",
        f"🌡 Різниця <b>{diff:.0f}°</b> — стільки градусів щастя нам винні!",
        sea_joke(sst),
    ]
    if wave is not None:
        lines.append(f"🌊 Хвилі {wave:.1f} м — " + ("штиль, можна плавати з коктейлем 🍹" if wave < 0.5 else "трохи гойдає, як нас від нетерпіння"))
    if sun_h:
        lines.append(f"☀️ Сонця сьогодні там {sun_h:.0f} год, захід о {sunset} — без нас, але скоро з нами 🌅")
    lines += ["", f"💬 <i>{SLOGANS[days % len(SLOGANS)]}</i>", "", f"📅 Виліт: {TARGET.strftime('%d.%m.%Y о %H:%M')}"]
    return "\n".join(lines)


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
