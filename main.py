from flask import Flask, render_template, jsonify, request
import time
import requests

app = Flask(__name__)

# --- НАЛАШТУВАННЯ TELEGRAM ---
TELEGRAM_TOKEN = "8579627228:AAERKL8GXuICCDakodLHc5mNl_ZqRktsAek"
CHAT_ID = "8315278464"
known_ips = set() # Сюди записуємо унікальних гостей

market_state = {
    "btc_price": 0, "gold_price": 0, "silver_price": 0,
    "oil_price": 0, "dxy_index": 105.20,
    "signal": "WAIT", "status_code": "SYNC",
    "funding": 0, "last_update": 0
}

def send_tg_notification(ip):
    """Надсилає повідомлення в телеграм про нового гостя"""
    try:
        msg = f"🐼 *Panda Sentinel Alert*\n\nНовий відвідувач на сайті!\n📍 IP: `{ip}`"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

@app.route('/')
def index():
    # Отримуємо IP гостя
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if visitor_ip and visitor_ip not in known_ips:
        known_ips.add(visitor_ip)
        send_tg_notification(visitor_ip)
    
    return render_template('index.html')

@app.route('/api/pulse')
def get_pulse():
    if time.time() - market_state["last_update"] > 180 and market_state["last_update"] != 0:
        market_state["status_code"] = "OFFLINE"
    return jsonify(market_state)

@app.route('/api/update', methods=['POST'])
def update_data():
    data = request.json
    try:
        market_state.update({
            "btc_price": data.get("btc"),
            "gold_price": data.get("gold"),
            "silver_price": data.get("silver"),
            "oil_price": data.get("oil"),
            "dxy_index": data.get("dxy"),
            "funding": data.get("fund"),
            "last_update": time.time()
        })
        fund = market_state["funding"]
        if fund < -0.0010: market_state["signal"], market_state["status_code"] = "BUY", "BUY"
        elif fund > 0.0010: market_state["signal"], market_state["status_code"] = "SELL", "SELL"
        else: market_state["signal"], market_state["status_code"] = "WAIT", "FLAT"
        return {"status": "success"}, 200
    except: return {"status": "error"}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
