

from flask import Flask, request
import requests
import json
import html

app = Flask(__name__)

TELEGRAM_TOKEN = '8758305420:AAEVpelPYZWw7_kNNX4rruPbh_Zx9mYcmDU'
TELEGRAM_CHAT_ID = '1175507076'
AMO_DOMAIN = 'vladaslamov.amocrm.ru'  # подставьте свой

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

@app.after_request
def disable_ngrok_warning(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response
    
@app.route('/')
def home():
    return "OK", 200
    
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    # данные приходят в form
    data = request.form.to_dict()
    if not data:
        return "OK", 200

    # Логирование (можно удалить после отладки)
    print("\n=============== ВХОДЯЩИЙ ВЕБХУК ===============")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("================================================\n")

    # Ищем все сообщения: перебираем индексы
    i = 0
    while True:
        text_key = f'message[add][{i}][text]'
        if text_key not in data:
            break

        text = data.get(text_key)
        msg_type = data.get(f'message[add][{i}][type]')  # "incoming" или "outgoing"
        author_name = data.get(f'message[add][{i}][author][name]')
        origin = data.get(f'message[add][{i}][origin]', '')
        contact_id = data.get(f'message[add][{i}][contact_id]')  # может пригодиться для будущего поиска телефона

        # Телефон - в вебхуке не передаётся, можно будет получить через API по contact_id
        phone = "Не определен"  # или заглушка

        # Определяем роль по типу сообщения
        if msg_type == "incoming":
            role_icon = "👤"
            name = author_name or "КЛИЕНТ"
            title = f"<b>КЛИЕНТ: {html.escape(name)}</b>\n📞 <code>{html.escape(phone)}</code>"
        else:
            role_icon = "💼"
            name = author_name or "Менеджер"
            title = f"<b>МЕНЕДЖЕР: {html.escape(name)}</b>"

        # Источник
        origin_lower = origin.lower()
        if 'telegram' in origin_lower or 'tg' in origin_lower:
            source_label = "🔵 Telegram"
        elif 'whatsapp' in origin_lower:
            source_label = "🟢 WhatsApp"
        else:
            source_label = f"🔌 {origin}"

        # Ссылка на сделку (entity_id – это ID сделки)
        entity_id = data.get(f'message[add][{i}][entity_id]')
        if entity_id:
            deal_link = f"🔗 <a href='https://{AMO_DOMAIN}/leads/detail/{entity_id}'>Открыть сделку</a>"
        else:
            deal_link = ""

        msg = (
            f"{source_label}\n"
            f"---------------------------\n"
            f"{role_icon} {title}\n\n"
            f"💬 <b>Сообщение:</b>\n{html.escape(text)}\n\n"
            f"{deal_link}"
        )
        send_to_telegram(msg)
        i += 1

    return "OK", 200

if __name__ == '__main__':
    app.run(port=5000)
