"""
Бот для кофейни GRAIN на чистом Python (без сторонних библиотек!).
Запускается сразу: python bot.py
"""

import json
import os
import time
import threading
import urllib.request
import urllib.parse
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler

# ТОКЕН ТВОЕГО БОТА ИЗ @BotFather
BOT_TOKEN = "9047833133:AAHSaoU0w6B8rCQ5yCoCeCsjohX3Fvkp7NM"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ТВОЙ РЕАЛЬНЫЙ ОПУБЛИКОВАННЫЙ САЙТ НА NETLIFY С HTTPS!
MINI_APP_URL = "https://wondrous-paletas-1da71c.netlify.app"

# Крошечный веб-сервер для бесплатного тарифа Render.com
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<h1>GRAIN Coffee Bot is Running 24/7!</h1>")

    def log_message(self, format, *args):
        pass  # Отключаем лишний спам в консоль

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Отключаем строгую проверку SSL на случай корпоративных прокси
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def call_telegram(method: str, data: dict = None) -> dict:
    """Универсальная функция для отправки команд в Telegram Bot API"""
    url = f"{API_URL}/{method}"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[Ошибка запроса к Telegram]: {e}")
        return {}


def setup_menu_button():
    """Устанавливает постоянную нативную кнопку 'Меню' в нижнем левом углу чата"""
    menu_data = {
        "menu_button": {
            "type": "web_app",
            "text": "☕ Меню GRAIN",
            "web_app": {
                "url": MINI_APP_URL
            }
        }
    }
    result = call_telegram("setChatMenuButton", menu_data)
    if result.get("ok"):
        print("✅ Постоянная кнопка меню в Telegram успешно настроена!")


def send_welcome(chat_id: int, user_first_name: str):
    """Отправляет приветствие и кнопку открытия Mini App"""
    text = (
        f"☕ *Добро пожаловать в GRAIN, {user_first_name}!*"
        "\n\n"
        "Мы обжариваем спешелти зерно свежего урожая и варим чистый, сбалансированный кофе.\n\n"
        "Нажмите кнопку ниже, чтобы открыть интерактивное меню и заказать кофе прямо в Telegram 👇"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "☕ Открыть меню GRAIN",
                    "web_app": {"url": MINI_APP_URL}
                }
            ],
            [
                {
                    "text": "📍 О нашей кофейне",
                    "callback_data": "about"
                }
            ]
        ]
    }

    call_telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    })


def send_about(chat_id: int):
    """Информация о кофейне"""
    text = (
        "🏛 *Кофейня и ростерия GRAIN*\n\n"
        "📍 ул. Кофейная, 10\n"
        "⏰ Ежедневно с 08:00 до 22:00\n"
        "🌿 Только 100% арабика класса Specialty (Q-грейд 85+)\n\n"
        "Готовим напитки на зерне собственной обжарки."
    )
    call_telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })


def handle_order(chat_id: int, order_json_str: str):
    """Обрабатывает заказ, пришедший из Mini App"""
    try:
        data = json.loads(order_json_str)
        items = data.get("items", [])
        total = data.get("totalPrice", 0)
        formatted_total = data.get("formattedTotal", f"{total} ₸")
        pickup = data.get("pickup", "Как можно скорее")

        items_formatted = "\n".join([f"• {item}" for item in items])

        response_text = (
            "🎉 *Заказ успешно оформлен в GRAIN!*\n\n"
            f"*Состав заказа:*\n{items_formatted}\n\n"
            f"*Готовность:* {pickup}\n"
            f"*Сумма к оплате:* {formatted_total}\n\n"
            "⏳ Бариста уже получил ваш чек и начал готовить напитки. Сообщим, когда заказ будет готов!"
        )

        call_telegram("sendMessage", {
            "chat_id": chat_id,
            "text": response_text,
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print(f"[Ошибка разбора заказа]: {e}")


def main():
    print("=" * 60)
    print("🚀 Бот кофейни GRAIN запущен и ждет клиентов...")
    print(f"👉 Открой Telegram и напиши боту: @grain_coffee_bot")
    print(f"🌐 Mini App URL: {MINI_APP_URL}")
    print("=" * 60)

    # Проверяем авторизацию
    me = call_telegram("getMe")
    if me.get("ok"):
        print(f"Авторизован как: @{me['result']['username']} ({me['result']['first_name']})")
    else:
        print("Не удалось авторизоваться. Проверь токен!")
        return

    # Настраиваем постоянную кнопку "Меню" в углу чата
    setup_menu_button()

    # Запускаем фоновый веб-сервер для Render
    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()
    print("🌐 Health-check сервер запущен для Render")

    offset = 0

    # Бесконечный цикл опроса Telegram (Long Polling)
    while True:
        try:
            updates = call_telegram("getUpdates", {"offset": offset, "timeout": 20})
            if not updates.get("ok"):
                time.sleep(2)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1

                # Обработка нажатий на инлайн-кнопки
                if "callback_query" in update:
                    cq = update["callback_query"]
                    chat_id = cq["message"]["chat"]["id"]
                    data = cq.get("data")
                    if data == "about":
                        send_about(chat_id)
                    call_telegram("answerCallbackQuery", {"callback_query_id": cq["id"]})
                    continue

                # Обработка сообщений
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    user_name = msg.get("from", {}).get("first_name", "Гость")

                    # Проверяем, пришел ли заказ из Mini App
                    if "web_app_data" in msg:
                        raw_data = msg["web_app_data"]["data"]
                        print(f"Получен заказ от {user_name}: {raw_data}")
                        handle_order(chat_id, raw_data)
                        continue

                    text = msg.get("text", "")
                    if text.startswith("/start"):
                        send_welcome(chat_id, user_name)
                    elif text.startswith("/help"):
                        call_telegram("sendMessage", {
                            "chat_id": chat_id,
                            "text": "Нажмите /start, чтобы открыть главное меню кофейни!"
                        })

        except KeyboardInterrupt:
            print("\nБот остановлен вручную.")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
